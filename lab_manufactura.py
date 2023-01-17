from pydexarm import Dexarm
import random
import requests
import base64
import json
import time
import threading

class manufacturing_laboratory():
    #Constructor
    def __init__(self, username = "iotadmin.00179", password ="", port_arm1= "COM13" , port_arm2 = "COM14", url_airpicker ="",url_laser ="",url_belt =""):
        self.username = username
        self.password = password
        self.port_arm1 = port_arm1
        self.port_arm2 = port_arm2
        self.url_airpicker = url_airpicker
        self.url_laser = url_laser
        self.url_belt = url_belt
        self.headers = ""
        self.start_time_process = 0
        self.cronometer_running = False


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

    def block_production(self, gcode_path='RESET_POINT.txt', arm=1):
        if arm == 1:
            dexarm = Dexarm(port=self.port_arm1)
        if arm == 2:
            dexarm = Dexarm(port=self.port_arm2)
        if arm == 3:
            dexarm = Dexarm(port=self.port_arm2)
            gcode_path = self.quality_control()

        gcode_file = open(gcode_path, 'r')
        while True: 
            line = gcode_file.readline()
            if not line:
                break
            command = line.strip() + '\r'
            print(command)
            dexarm._send_cmd(command)
        gcode_file.close()

        return True

    def quality_control(self):
        gcode_path =''
        k = random.random()
        print(k)
        if k > 0.2:
            gcode_path = 'BELT_MOVEMENT_POS.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="block approved")
        else:
            gcode_path = 'BELT_MOVEMENT_NEG.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="block rejected")
        return gcode_path

    def api_monitor(self, url="", machine_id="airpicker1",  status="off"): 

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
        # self.block_production("ORACLE_LASER.txt",2)
        print("gravando laser")
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="finish graving")
        self.block_production("LASER_MOVEMENT_FINISH.txt",2)
        self.api_monitor(url= self.url_laser, machine_id="laser1", status="off")

        #Pick bloxk and set it to quality control station
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="block collocation for quality control")
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpicker1", status="off")

        #Quality control
        self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="checking block")
        self.block_production(arm=3)
        self.api_monitor(url= self.url_belt, machine_id="qualitycontrol1", status="off")

        return "Finish block"
    
    def start_process(self):
        # Start the cronometer
        self.cronometer_running = True

        thread = threading.Thread(target=self.cronometer)
        thread.start()

        # Run the production line
        production_line = self.production_line()
        
        # Finish the cronometer
        self.cronometer_running = False
        thread.join()

        return f" {production_line} in: {self.start_time_process:.2f} seconds"

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

        json_data_1 = json.dumps(data_1)
        json_data_2 = json.dumps(data_2)
        json_data_3 = json.dumps(data_3)

        print(json_data_1)
        response_1 = requests.post(url=self.url_airpicker, headers=self.headers, data=json_data_1, verify=False)
        print(response_1)
        print(json_data_2)
        response_2 = requests.post(url=self.url_laser, headers=self.headers, data=json_data_2, verify=False)
        print(response_2)
        print(json_data_3)
        response_3 = requests.post(url=self.url_belt, headers=self.headers, data=json_data_3, verify=False)
        print(response_3)
        return True
        

url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Quality_Control_Connector"
url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Airpicker_Connector"
url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Laser_Connector"
manufactory = manufacturing_laboratory(username = "iotadmin.00179", password ="2D#To8JUZ6qN", port_arm1= "COM13" , port_arm2 = "COM14", url_airpicker =url_link_airpicker,url_laser =url_link_laser,url_belt = url_link_qualitycontrol)

print(manufactory.testing_api())