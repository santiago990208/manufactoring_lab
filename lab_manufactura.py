from pydexarm import Dexarm
from sense_hat import SenseHat
import random
import requests
import base64
import json
import time
import threading

class manufacturing_laboratory():
    #Constructor
    def __init__(self, username = "", password ="", to_produce = "",port_arm1= "" , port_arm2 = "", url_airpicker ="",url_laser ="",url_belt ="", url_vibration ="", url_counter_aproved = "", url_counter_rejected = ""):
        self.username = username
        self.password = password
        self.to_produce = to_produce
        self.port_arm1 = port_arm1
        self.port_arm2 = port_arm2
        self.url_airpicker = url_airpicker
        self.url_laser = url_laser
        self.url_belt = url_belt
        self.url_vibration = url_vibration
        self.url_counter_aproved = url_counter_aproved
        self.url_counter_rejected = url_counter_rejected
        self.headers = ""
        self.start_time_process = 0
        self.cronometer_running = False
        self.sensor_running = False
        self.count_approved = 0
        self.count_rejected = 0
        self.accelerometer = 0
        self.error_production = 0


    def conf_api_headers(self):
        # Encode the username and password
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode("utf-8")
        b64_auth_string = base64.b64encode(auth_bytes).decode("utf-8")

        self.headers = {
            "Authorization": f"Basic {b64_auth_string}",
            "Content-Type": "application/json"
        }

        print(self.headers)

        return self.headers

    def cronometer(self):
        # Run the timer until the function finishes
        start_time = time.perf_counter()
        
        while self.cronometer_running:
            self.start_time_process = time.perf_counter() - start_time
            time.sleep(0.5)

    def vibration(self):
        # Run the senser vibration in a new thread
        sense = SenseHat()
        sense.show_message("Starting")
        while self.sensor_running:
            self.accelerometer = sense.get_accelerometer_raw()
            x = self.accelerometer["x"]
            y = self.accelerometer["y"]
            z = self.accelerometer["z"]
            #print("x: {0},y: {1}, z: {2}".format(x,y,z))
            self.accelerometer = max(x, y, z)
            if self.accelerometer > 1.5:
                self.error_production += 1
                self.api_monitor(url = self.url_vibration, machine_id="graving_base", accelerometer = self.accelerometer)
                sense.clear((255,0,0))
            else:
                sense.clear((0,255,0))

    def block_production(self, gcode_path='RESET_POINT.txt', arm=1, count = 1):
        if arm == 1:
            dexarm = Dexarm(port=self.port_arm1)
        if arm == 2:
            dexarm = Dexarm(port=self.port_arm2)
        if arm == 3:
            dexarm = Dexarm(port=self.port_arm2)
            gcode_path = self.quality_control(count)

        gcode_file = open(gcode_path, 'r')
        while True: 
            line = gcode_file.readline()
            if not line:
                break
            command = line.strip() + '\r'
            #print(command)
            dexarm._send_cmd(command)
        gcode_file.close()

        return True

    def quality_control(self, count):
        gcode_path =''
        if self.error_production == 0:
            self.count_approved += 1
            gcode_path = 'BELT_MOVEMENT_POS.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="block approved")
            self.api_monitor(url= self.url_counter_aproved, machine_id="counter_aproved", counter=self.count_approved)
        else:
            self.count_rejected += 1
            gcode_path = 'BELT_MOVEMENT_NEG.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="block rejected")
            self.api_monitor(url= self.url_counter_rejected, machine_id="counter_rejected", counter=self.count_rejected)
        return gcode_path

    def api_monitor(self, url="", machine_id="airpicker1",  status="off", counter="", accelerometer = ""): 

        if counter != "":
            data = {
                "id": machine_id,
                "counter":counter,
                "start_time_process":  f"{self.start_time_process:.2f}",
            }
        elif accelerometer != "":
            data = {
                "id": machine_id,
                "accelerometer":accelerometer,
                "start_time_process":  f"{self.start_time_process:.2f}",
            }
        else:
            data = {
                "id": machine_id,
                "status":status,
                "start_time_process": f"{self.start_time_process:.2f}",
            }

        json_data = json.dumps(data)
        response = requests.post(url, headers=self.headers, data=json_data, verify=False)
        print(response.status_code)
        return True

    def production_line(self):
        #Set init point
        self.block_production()
        self.block_production(arm=2)
        self.conf_api_headers()
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="off")
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="off")
        self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="off")

        #Choose block and set to graving station
        
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="block collocation for graving")
        self.block_production('BLOCK_MOVEMENT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="off")

        #Graving station
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="on")
        self.block_production("LASER_MOVEMENT_START.txt",2)
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="graving")
        
        #agregar vibracion de sensor en el laser para que no gabre el segundo 
        if self.error_production == 0:
            self.block_production("IoT.txt",2)
            print("gravando laser")
            
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="finish graving")
        self.block_production("LASER_MOVEMENT_FINISH.txt",2)
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="off")

        #Pick block and set it to quality control station
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="block collocation for quality control")
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="off")

        #Quality control
        self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="checking block")
        self.block_production(arm=3)
        self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="off")

        return True
    
    def start_process(self):
        # Start the cronometer
        in_production = 1
        for in_production in range(self.to_produce):
            self.cronometer_running = True
            self.sensor_running = True
            thread_cronometer = threading.Thread(target=self.cronometer)
            thread_cronometer.start()
            thread_sensor = threading.Thread(target=self.vibration)
            thread_sensor.start()
            # Run the production line 1
            self.testing_production_line()
            # Finish the cronometer
            self.cronometer_running = False
            self.sensor_running = False
            thread_cronometer.join()
            thread_sensor.join()

            print(f" Acce: {self.accelerometer},  Errors: {self.error_production} , Appro: {self.count_approved}, Rejec: {self.count_rejected}")
            print(f" Finished {in_production} blocks in: {self.start_time_process:.2f} seconds")
            in_production += 1
            
        return (f" The production of {self.to_produce} has finished in {self.start_time_process:.2f} seconds , there are {self.count_approved} approved blocks and {self.count_rejected} rejected blocks, the line process detected {self.error_production} errors")

    def testing_api(self):
        print(self.headers)
        data_1 = {
            "id": "airpicker1",
            "status":"off",
            "start_time_process": "2",
        }
        data_2 = {
            "id": "laser1",
            "status":"off",
            "start_time_process": "2",
        }
        data_3 = {
            "id": "qualitycontrol1",
            "status":"off",
            "start_time_process": "2",
        }
        data_4 = {
            "id": "counter_aproved",
            "counter":"1",
            "start_time_process": "2",
        }
        data_5 = {
            "id": "counter_rejected",
            "counter":"1",
            "start_time_process": "2",
        }

        json_data_1 = json.dumps(data_1)
        json_data_2 = json.dumps(data_2)
        json_data_3 = json.dumps(data_3)
        json_data_4 = json.dumps(data_4)
        json_data_5 = json.dumps(data_5)

        print(json_data_1)
        response_1 = requests.post(url=self.url_airpicker, headers=self.headers, data=json_data_1, verify=False)
        print(response_1)

        print(json_data_2)
        response_2 = requests.post(url=self.url_laser, headers=self.headers, data=json_data_2, verify=False)
        print(response_2)

        print(json_data_3)
        response_3 = requests.post(url=self.url_belt, headers=self.headers, data=json_data_3, verify=False)
        print(response_3)

        print(json_data_4)
        response_4 = requests.post(url=self.url_belt, headers=self.headers, data=json_data_4, verify=False)
        print(response_4)

        print(json_data_5)
        response_5 = requests.post(url=self.url_belt, headers=self.headers, data=json_data_5, verify=False)
        print(response_5)

        return True
    
    def testing_production_line(self):
        #Set init point
        self.block_production()
        self.block_production(arm=2)
        self.conf_api_headers()

        #Choose block and set to graving station
        
        self.block_production('BLOCK_MOVEMENT.txt',1)

        #Graving station
        self.block_production("LASER_MOVEMENT_START.txt",2)
        
        #agregar vibracion de sensor en el laser para que no gabre el segundo 
        print("entering to condition ")
        print(self.error_production)
        if self.error_production == 0:
            self.block_production("IoT.txt",2)
            print("gravando laser")
            
        self.block_production("LASER_MOVEMENT_FINISH.txt",2)
        

        #Pick block and set it to quality control station
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        #Quality control
        self.block_production(arm=3)

        return True


