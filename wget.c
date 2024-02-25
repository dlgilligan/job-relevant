
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/stat.h>

#define BUFFER_SIZE 1024

// Function to send a GET request and create a local file without the HTTP response header (if the response is 200).
int downloadFile(const char *host, int port, const char *path) {
    int fd;
    struct sockaddr_in server_addr;
    struct hostent *server;

    // Create a socket
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return -1;
    }

    // Resolve the host
    server = gethostbyname(host);
    if (server == NULL) {
        close(fd);
        return -1;
    }

    // Prepare server address structure
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    bcopy((char *)server->h_addr, (char *)&server_addr.sin_addr.s_addr, server->h_length);

    // Connect to the server
    if ((connect(fd, (struct sockaddr *)&server_addr, sizeof(server_addr))) < 0) {
        close(fd);
        return -1;
    }

    // Send the GET request
    char request[256];
    snprintf(request, sizeof(request), "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n", path, host, port);
    if (send(fd, request, strlen(request), 0) < 0) {
        close(fd);
        return -1;
    }

    // Receive and process the response
    char buffer[BUFFER_SIZE];
    ssize_t bytes;
    int content_length = -1;
    int code = 0;
    int header_parse = 0;
    int data_recv = 0;
    FILE *local_file = NULL;
    char local_fname[256];

    while ((bytes = recv(fd, buffer, sizeof(buffer), 0)) > 0) {
        // Extract the HTTP response code
        if (code == 0 && sscanf(buffer, "HTTP/1.1 %d", &code) == 1) {
            if (code != 200) {
                // If the response code is not 200, print the first line of the header
                header_parse = 1;
                printf("%.*s", (int)(strchr(buffer, '\n') - buffer), buffer);
                return -1;
            }
        }

        // Check if Content Length header is present
        if (content_length == -1) {
            char *content_length_ptr = strstr(buffer, "Content-Length: ");
            if(content_length_ptr) {
                content_length = atoi(content_length_ptr + 16);
            }
        }

        if (!header_parse) {
            char *header_end = strstr(buffer, "\r\n\r\n");
            if (header_end) {
                // The header is fully received
                header_parse = 1;

                if(content_length == -1) {
                    printf("Error: could not download the requested file (file length unknown)");
                    close(fd);
                    return -1;
                }

                if (code == 200) {
                    // Extract the filename from the path
                    char *filename_start = strrchr(path, '/');
                    if (filename_start == NULL) {
                        filename_start = (char *)path;
                    } else {
                        filename_start++; // Skip the '/' character
                    }

                    snprintf(local_fname, sizeof(local_fname), "%s", filename_start);
                    local_file = fopen(local_fname, "wb");

                    if (local_file == NULL) {
                        close(fd);
                        return -1;
                    }

                    // Calculate the position of the data, skip the header
                    size_t header_length = header_end - buffer + 4;
                    size_t data_sz = bytes - header_length;

                    // Write the data portion to the local file
                    if (data_sz > 0) {
                        if (fwrite(buffer + header_length, sizeof(char), data_sz, local_file) != data_sz) {
                            close(fd);
                            fclose(local_file);
                            return -1;
                        }
                        data_recv = data_sz;
                    }
                }
            }
        } else {
            // Write the entire buffer to the local file
            if (fwrite(buffer, sizeof(char), bytes, local_file) != bytes) {
                close(fd);
                fclose(local_file);
                return -1;
            }
            data_recv += bytes;
        }
    }

    if (bytes < 0) {
        close(fd);
        if (local_file) {
            fclose(local_file);
        }
        return -1;
    }

    // Close the socket and the local file
    close(fd);
    if (local_file) {
        fclose(local_file);
    }

    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "usage: ./http_client [host] [port number] [filepath]\n");
        exit(1);
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    const char *path = argv[3];

    if (downloadFile(host, port, path) != 0) {
        return 1;
    }

    return 0;
}
