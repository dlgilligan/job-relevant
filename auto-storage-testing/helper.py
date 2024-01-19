
def read_property(key,file_path):
    file = open(file_path,'r')

    for line in file:
        if key == line.split('=')[0]:
            file.close()
            return line.split('=')[1]
    file.close()
    return -1

def byte_conversion(var):
    var = var.split(' ')

    match(var[1]):
        case 'MB':
            return 1000 * int(var[0])
        case 'GB':
            return 1000000 * int(var[0])

