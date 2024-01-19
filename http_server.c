/* The code is subject to Purdue University copyright policies.
 * DO NOT SHARE, DISTRIBUTE, OR POST ONLINE
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>


#define BUFFER_SIZE 4096
#define WEB_ROOT "Webpage"
#define LISTEN_QUEUE 50 /* Max outstanding connection requests; listen() param */
#define DBADDR "127.0.0.1"

void replace_plus_with_space(char* str) {
    for (int i = 0; str[i] != '\0'; ++i) {
        if (str[i] == '+') {
            str[i] = ' ';
        }
    }
}

void handle_request(int client_socket, struct sockaddr_in client_address, int db_port) {
    char buffer[BUFFER_SIZE];
    ssize_t bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);
    buffer[bytes_received] = '\0';

    // Split the request into individual lines
    char *request_lines[3];
    request_lines[0] = strtok(buffer, "\r\n");
    for (int i = 1; i < 3; i++) {
        request_lines[i] = strtok(NULL, "\r\n");
    }

    // Extract method, URI, and protocol from the first line
    char method[10], uri[255], protocol[20];
    sscanf(request_lines[0], "%s %s %s", method, uri, protocol);

    // Log the request to the terminal
    printf("%s \"%s\" ", inet_ntoa(client_address.sin_addr), request_lines[0]);

    // Initialize the status code to 200 OK
    int status_code = 200;


    // Reject any non HTTP/1.0, HTTO/1.1, or GET requests
    if ((strcmp(protocol, "HTTP/1.0") != 0 && strcmp(protocol, "HTTP/1.1") != 0) || strcmp(method, "GET") != 0) {
        status_code = 501;
        printf("501 Not Implemented\n");
        
        // Respond
        dprintf(client_socket, "HTTP/1.0 501 Not Implemented\r\n\r\n<html><body><h1>501 Not Implemented</h1></body></html>");
        
        // Close the connection
        close(client_socket);
        return;
    }

    // Check if the URI starts with a "/"
    if (uri[0] != '/') { // Bad Request
        status_code = 400;

        // Respond
        printf("400 Bad Request\n");
        dprintf(client_socket, "HTTP/1.0 400 Bad Request\r\n\r\n<html><body><h1>400 Bad Request</h1></body></html>");

        // Close the connection
        close(client_socket);
        return;
    } else if (strstr(uri, "?key=") != NULL) { // DB Request
        // Extract the search string from the URI
        char search_string[255];
        char *search_param = strstr(uri,"?key=");
        sscanf(search_param, "?key=%s", search_string);
        replace_plus_with_space(search_string);

        // Communicate with the database server
        int db_socket = socket(AF_INET, SOCK_DGRAM, 0);
        struct sockaddr_in db_server_address;
        db_server_address.sin_family = AF_INET;
        db_server_address.sin_addr.s_addr = inet_addr(DBADDR);
        db_server_address.sin_port = htons(db_port);

        // Send the search string to the database server
        sendto(db_socket, search_string, strlen(search_string), 0, (struct sockaddr *)&db_server_address, sizeof(db_server_address));

        // Use select to implement a timeout
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(db_socket, &read_fds);

        struct timeval timeout;
        timeout.tv_sec = 5;
        timeout.tv_usec = 0;

        int select_result = select(db_socket + 1, &read_fds, NULL, NULL, &timeout);

        // Evaluate DB response
        if (select_result > 0) {
            ssize_t bytes_read;

            // Receive data from the database server
            bytes_read = recv(db_socket, buffer, sizeof(buffer), 0);

            // Check if it indicates a file not found
            if (bytes_read > 0 && bytes_read < sizeof(buffer) && strstr(buffer, "File Not Found") != NULL) {
                status_code = 404;

                // Send the appropriate header for a not found error
                printf("404 Not Found\n");
                dprintf(client_socket, "HTTP/1.0 404 Not Found\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>");

                // Close Connections
                close(db_socket);
                close(client_socket);
                return;
            }

            // Send the appropriate header for a successful response
            dprintf(client_socket, "HTTP/1.0 200 OK\r\nContent-Length: -1\r\n\r\n");

            // Continue receiving and sending the data in chunks
            while (1) {
                // Check if it indicates the final UDP packet
                if (bytes_read < sizeof(buffer) && strstr(buffer, "DONE") != NULL) {
                    break;
                }

                // Send the data over the connection
                ssize_t bytes_sent = send(client_socket, buffer, bytes_read, 0);

                if (bytes_sent < 0) {
                    // Handle send error if needed
                    break;
                }

                // Receive the next chunk of data
                bytes_read = recv(db_socket, buffer, sizeof(buffer), 0);

                if (bytes_read < 0) {
                    // Handle receive error if needed
                    break;
                }
            }
        } else if (select_result == 0) {
            status_code = 408;

            // Respond with appropriate header
            printf("408 Request Timeout\n");
            dprintf(client_socket, "HTTP/1.0 408 Request Timeout\r\n\r\n<html><body><h1>408 Request Timeout</h1></body></html>");
        }

        // Close the connection
        close(db_socket);
    } else { // File Path Request
        // Combine the URI with the Web Root
        char file_path[255 + strlen(WEB_ROOT)];
        snprintf(file_path, sizeof(file_path), "%s%s", WEB_ROOT, uri);

        // Check for security risks in the URI
        if (strstr(uri, "/../") != NULL || strcmp(uri + strlen(uri) - 3, "/..") == 0) {
            status_code = 400;

            // Respond
            printf("400 Bad Request\n");
            dprintf(client_socket, "HTTP/1.0 400 Bad Request\r\n\r\n<html><body><h1>400 Bad Request</h1></body></html>");

            // Close the connection
            close(client_socket);
            return;
        } else {
            // If the URI ends with a "/", treat it as index.html
            if (uri[strlen(uri) - 1] == '/') {
                strcat(file_path, "index.html");
            }

            // Check if the path is a directory and append "index.html"
            struct stat path_stat;
            if (stat(file_path, &path_stat) == 0 && S_ISDIR(path_stat.st_mode)) {
                strcat(file_path, "/index.html");
            }

            // Try to open the file
            int file_descriptor = open(file_path, O_RDONLY);
            if (file_descriptor == -1) {
                status_code = 404;
                
                // Respond
                printf("404 Not Found\n");
                dprintf(client_socket, "HTTP/1.0 404 Not Found\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>");

                // Close the connection
                close(client_socket);
                return;
            } else {
                // Respond with 200 OK and send the file in chunks
                dprintf(client_socket, "HTTP/1.0 200 OK\r\n\r\n");
                ssize_t bytes_read;
                while (((bytes_read = read(file_descriptor, buffer, sizeof(buffer))) > 0)) {
                    send(client_socket, buffer, bytes_read, 0);
                }
                close(file_descriptor);
            }
        }
    }

    // Log the response status
    if (status_code == 200) {
        printf("200 OK\n");
    }

    // Close the connection
    close(client_socket);

    return;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        fprintf(stderr, "usage: ./http_server [server port] [DB port]\n");
        exit(1);
    }

    int server_port = atoi(argv[1]);
    int db_port = atoi(argv[2]);

    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in server_address, client_address;
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = INADDR_ANY;
    server_address.sin_port = htons(server_port);

    if(bind(server_socket, (struct sockaddr *)&server_address, sizeof(server_address)) == -1) {
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Set maximum number of outstanding connection requests

    if(listen(server_socket, LISTEN_QUEUE) == -1) {
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    while (1) {
        socklen_t client_address_len = sizeof(client_address);
        int client_socket = accept(server_socket, (struct sockaddr *)&client_address, &client_address_len);

        if(client_socket == -1) {
            continue;
        }

        // Handle Request
        handle_request(client_socket, client_address, db_port);
    }

    close(server_socket);

    return 0;
}
