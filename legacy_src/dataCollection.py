from pyparrot.Minidrone import Mambo, Minidrone
import pyparrot
from pyparrot.commandsandsensors.DroneSensorParser import DroneSensorParser

mamboMac = "7A:64:62:66:4B:67"
mac = "D0:3A:49:F7:E6:22"
mambo_bluetooth_adress = "84:20:96:6c:22:67"#"80:19:34:EB:35:56" #"84:20:96:6c:22:67" 
mambo = Mambo(mac.islower(), use_wifi=False)
# mambo = Mambo(mambo_bluetooth_adress.islower(), use_wifi=False)
print("trying to connect")

success = mambo.connect(num_retries=3)
print(f""" connected >>>> {success}""")

if success:
    print("sleeping")
    mambo.smart_sleep(2)

    print("getting status")
    mambo.ask_for_state_update()
    mambo.smart_sleep(2)

    # mambo.set_user_sensor_callback
    # print("end of getting status")


    print(f'''battery status is {mambo.sensors.battery}''')
    print(f'''flying status is {mambo.sensors.flying_state}''')


    print(f'''X is {mambo.sensors.quaternion_x}''')
    print(f'''Y is {mambo.sensors.quaternion_y}''')
    print(f'''Z is {mambo.sensors.quaternion_z}''')


    print("disconnect")
    mambo.disconnect()


    
