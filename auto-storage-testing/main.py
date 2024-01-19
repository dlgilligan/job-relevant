import os
import subprocess
import helper
#import Broadcom
#import Adaptec

vendors = ["Broadcom","Adaptec"]

def read_config(filename='config.txt'):
    config_file = open(filename,'r')
    ret=[]

    for line in config_file:
        if line.count('=') > 0:
            ret.append(line.split('=')[1])

    config_file.close()

    return ret
        


def Vendor():
    result = subprocess.run("lspci -knn | grep 'RAID bus controller'", stdout=subprocess.PIPE)
    result = result.stdout.decode('utf-8')

    for i in vendors:
        if i in result == True:
            return i
        else:
            return -1


if __name__ == '__main__'
    c_Vendor = Vendor()

    test_configs = read_config()

    levels = test_configs[0].strip().split(',') #
    strips = test_configs[1].strip().split(',') #
    drives = test_configs[2].strip().split(',') #
    block_sizes = test_configs[3].strip().split(',')
    write_c = test_configs[4].strip().split(',')
    tests = test_configs[5].strip().split(',')

    if c_Vendor == "Broadcom":
        for i in levels:
            for j in drives:
                for k in strips:
                    for l in block_sizes:
                        for m in tests:
                            for n in write_c:
                                # Broadcom(i,j,k,l,m,n,o)
    elif c_Vendor == "Adaptec":
        for i in levels:
            for j in drives:
                for k in strips:
                    for l in block_sizes:
                        for m in tests:
                            for n in write_c:
                                # Adaptec(i,j,k,l,m,n,o)
    else: 
        print("Vendor is not supported by the program")


