import os
import subprocess
import helper
from time import sleep
import re

def Wipe(drives): # Returns the name of the queue scheduler profile to be used

  os.system("storcli64 /c0 delete config") # Clear the configuration
  os.system("storcli64 /c0/e252/sall set good") # Set all drives to good

  drive_properties=subprocess.run("storcli64 /c0/e252/s0 show | sed -n '14 p'", stdout=subprocess.PIPE) # Run command and extract the output
  drive_properties=drive_properties.stdout.decode('utf-8') # Decode the output to utf-8
  drive_properties=re.sub(' +', ' ',drive_properties) # Remove excess whitespace within the string
  drive_properties=drive_properties.strip().split(' ') # Remove leading and trailing whitespace, split on spaces into list of properties

  temp = drive_properties[8]
  if(temp == 'N'): # SED Disabled
      os.system("storcli64 /c0/e252/s0-"+drives-1+" start erase normal")

      while(True):
          temp = subprocess.run("storcli64 /c0/e252/s0-"+drives-1+" show erase | sed -n '12 p' | awk '{print $5}'",stdout=subprocess.PIPE)
          temp = temp.stdout.decode('utf-8')

          if(temp == '-'):
              break

          sleep(300)
  else:
      os.system("storcli64 /c0/e252/s0"+drives-1+" secureerase")
      sleep(10800) # Wait 3 Hours
      os.system("storcli64 /c0/e252/s0"+drives-1+" stop secureerase")
  
  return ""+drive_properties[6]+"_"+drive_properties[7]+".sh"



def Configure(drives,raid_level,strip_size,pdcache,scheduler_script): # Full raid level should be passed 'RAID5', strip size should be passed in KB
  f_temp='controller_properties.txt'

  os.system("storcli64 /c0 show all | sed -n '367,392p' > controller_properties.txt")

  temp = helper.read_property('RAID Level Supported ',f_temp) # Checking if the RAID level is supported by the controller
  if raid_level in temp == False:
      print(raid_level + " is not supported by the controller")
      return -1 # ERROR 

  temp = helper.read_property('Min Strip Size ',f_temp) # Checking if the Strip Size is above controller minimum
  if 'KB' in temp == True: # Controller min is listed in KB
      if strip_size < int(temp.strip().split(' ')[0]):
          print("Strip Size is below the controller minimum")
          return -1 # ERROR
  else: # Controller min is not listed in KB
      var = helper.byte_conversion(temp.strip())
      if strip_size < var:
          print("String size is below the controller minimum")
          return -1 # ERROR

  temp = helper.read_property('Max Strip Size ',f_temp) # Checking if the Strip Size is above controller maximum
  if 'KB' in temp == True: # Controller max is listed in KB
      if strip_size > int(temp.strip().split(' ')[0]):
          print("Strip Size is above the controller maximum")
          return -1 # ERROR
  else: # Controller max is not listed in KB
      var = helper.byte_conversion(temp.strip)
      if strip_size > var:
          print("Strip Size is above the controller maximum")
          return -1 # ERROR

  # Create the RAID configuration
  os.system("storcli64 /c0 add vd type="+raid_level.lower()+" name=test drives=252:0-"+drives-1+" pdcache="+pdcache)
  
  # Apply the Queue Scheduler Tunings
  os.system("q_Profiles/"+scheduler_script)

def Precondition(flag): # 0 = Sequential, 1 = Random
    if flag == 0:
        temp = os.system("fio fio_scripts/Preconditioning_SEQWrite.fio")
    else:
        temp = os.system("fio fio_scripts/RANWrite_Precon.fio")


def Broadcom(levels,drives,strips,block_sizes,tests,write_c):
    return 0
