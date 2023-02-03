from pydexarm import Dexarm
from rich import print
from sense_hat import SenseHat
import random
import requests
import base64
import json
import time
import threading
import datetime


class manufacturing_laboratory():
    #Constructor
    def __init__(self, username = "", password ="", org_id = "6BNYV2GM1F1G", port_arm1= "" , port_arm2 = "", url_api ="", url_airpicker ="",url_laser ="",url_belt ="", url_production_line = ""):
        
        #entry params
        self.username = username
        self.password = password
        self.org_id = org_id
        self.port_arm1 = port_arm1
        self.port_arm2 = port_arm2
        #api links
        self.url_api = url_api
        self.url_airpicker = url_airpicker
        self.url_laser = url_laser
        self.url_belt = url_belt
        self.url_production_line = url_production_line
        #init config variables
        self.headers = ""
        #threads boolean activators
        self.cronometer_running = False
        self.sensor_running = False
        self.workorder_listening = False
        #counters
        self.cronometer_time = 0
        self.error_production = 0
        self.work_order_processed = 0
        #rules
        self.max_vibration = 1.5 #put the max vibration to detect an error, it is a rule
        self.accelerometer = 0
        self.sense = SenseHat()
        #work order status and info
        self.start_time_proccess = datetime.datetime.utcnow()
        self.workorderId= ""
        self.factory = ""
        self.productId = ""
        self.to_produce = 0
        self.blockApproved = 0
        self.blockRejected = 0

    def conf_api_headers(self):
        # Encode the username and password
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode("utf-8")
        b64_auth_string = base64.b64encode(auth_bytes).decode("utf-8")

        self.headers = {
            "Authorization": f"Basic {b64_auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-ORACLE-IOT-ORG": self.org_id
        }

        return self.headers

    def cronometer(self):
        # Run the timer until the function finishes
        start_time = time.perf_counter()
        
        while self.cronometer_running:
            self.cronometer_time = time.perf_counter() - start_time
            time.sleep(0.01)

    def vibration(self):
        # Run the sensor vibration in a new thread
        while self.sensor_running:
            self.accelerometer = self.sense.get_accelerometer_raw()
            x = self.accelerometer["x"]
            y = self.accelerometer["y"]
            z = self.accelerometer["z"]

            self.accelerometer = max(x, y, z)
            if self.accelerometer > self.max_vibration:
                self.error_production += 1
                print(self.error_production)
                self.max_vibration = self.accelerometer
                self.sense.show_message(f"ERROR # {self.error_production}", text_colour=[255, 255, 255], back_colour=[255, 0, 0])
            else:
                self.sense.clear((0,150,0)) #green
                
    def workorder_start(self):    
        while self.workorder_listening:
            try:
                query = '?q={"systemState": { "$like":"RELEASED" } }'
                if self.url_api == "":
                    raise ValueError("The URL cannot be empty.")
                response = requests.get(self.url_api+query, headers=self.headers, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    workorder = data['items'][0] #brings the first to find
                    self.start_time_proccess  = datetime.datetime.utcnow()
                    
                    planned_start_time = datetime.datetime.fromtimestamp(round(workorder["plannedStartTime"] / 1000)) # format to compare wiuth now time

                    if self.start_time_proccess > planned_start_time:

                        self.workorderId = workorder["id"]
                        self.factory = workorder["factory"]
                        self.productId = workorder["product"]
                        self.to_produce = workorder["plannedQuantity"]
                        
                        if self.update_work_order(state="IN_PROCESS"):
                            print(f'send order of: {self.to_produce:.0f} blocks') #trigger production
                            self.testing_start()
                            self.workorder_listening = False #stops listening while the proccess is completed
                        else:
                            raise ValueError("Error on updating work order status")
                time.sleep(10)
            except ValueError as e:
                return print("An error occurred: ", e)
            except Exception as e:
                return print("An error occurred while sending the request: ", e)

    def update_work_order(self, state="IN_PROCESS"):
        try:
            workerOrder_id = f"/{self.workorderId}"
            if self.url_api == "":
                raise ValueError("The URL cannot be empty.")
            if state == "IN_PROCESS":
                data = {
                    "actualStartTime": int(time.time()),
                    "systemState": state,
                }
            if state == "COMPLETED":
                data = {
                    "actualEndTime": int(time.time()),
                    "systemState": "RELEASED", #COMPLETED
                }
            
            json_data = json.dumps(data)
            print(json_data)
            requests.post(self.url_api+workerOrder_id, headers=self.headers, data=json_data, verify=False)
            return True
        except ValueError as e:
            print("An error occurred: ", e)
            return False
        except Exception as e:
            print("An error occurred while sending the request: ", e)
            return False
        
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
            dexarm._send_cmd(command)
        gcode_file.close()

        return True

    def quality_control(self):
        gcode_path =''
        if self.error_production == 0:
            self.blockApproved += 1
            gcode_path = 'BELT_MOVEMENT_POS.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="INUSE", gravingCheck="Approved")
        else:
            self.blockRejected += 1
            gcode_path = 'BELT_MOVEMENT_NEG.txt'
            self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="INUSE", gravingCheck="Rejected")
        return gcode_path

    def api_monitor(self, url="", machine_id="airpickerState",  status="IDLE", accelerometer = "", gravingCheck=""): 
        try:
            if url == "":
                print("function send api")
                raise ValueError("The URL cannot be empty.")
        
            if machine_id == "airpickerState":
                data = {
                    "id": machine_id,
                    "state":status,
                }
            if machine_id == "laserState":
                data = {
                    "id": machine_id,
                    "state":status,
                    "accelerometer":accelerometer,
                }
            if machine_id == "qualityControl":
                data= {
                    "id": machine_id,
                    "factory": self.factory, #The value specified should be a registered factory identifier.
                    "state":status,
                    "product": self.productId, #Product identifier for the product that was produced
                    "quantity": self.blockApproved+self.blockRejected, #Quantity of the product produced.
                    "gravingCheck":gravingCheck,
                    "blockApproved": self.blockApproved,
                    "blockRejected": self.blockRejected,
                    "startTime":  int(self.start_time_proccess.timestamp),#add the start_time
                    "endTime":  int(time.time()),
                }

            json_data = json.dumps(data)
            print(json_data)
            requests.post(url, headers=self.headers, data=json_data, verify=False)
            return True
        except ValueError as e:
            return print("An error occurred: ", e)
        except Exception as e:
            return print("An error occurred while sending the request: ", e)

    def production_line(self):
        #Set init point
        self.block_production()
        self.block_production(arm=2)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")

        #Choose block and set to graving station
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.block_production('BLOCK_MOVEMENT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        #Graving station
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="INUSE", accelerometer=self.accelerometer)
        self.block_production("LASER_MOVEMENT_START.txt",2)
        
        #check if is there an error, it would not grave the block 
        if self.error_production == 0:
            self.block_production("IoT.txt",2)
            self.block_production("LASER_MOVEMENT_FINISH.txt",2)
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        else:
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="DOWN", accelerometer=self.accelerometer)
            self.block_production("LASER_MOVEMENT_FINISH.txt",2)
            
        #Pick block and set it to quality control station
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        #Quality control
        self.block_production(arm=3)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")

        return True
    
    def start_process(self):
        # Start the cronometer
        self.cronometer_running = True
        thread_cronometer = threading.Thread(target=self.cronometer)
        thread_cronometer.start()
        self.sense.show_message("Starting work order",text_colour=[0, 255, 255], back_colour=[25, 25, 25])
        for in_production in range(1,self.to_produce+1):
            self.sense.show_message(f"Block # {in_production}", text_colour=[255, 135, 0], back_colour=[25, 25, 25])
            
            self.sensor_running = True
            thread_sensor = threading.Thread(target=self.vibration)
            thread_sensor.start()
            # Run the production line 1
            self.production_line()
            
            self.sensor_running = False
            thread_sensor.join()

            self.sense.show_message(f" Finished {in_production} blocks in: {self.cronometer_time:.2f} seconds",  text_colour=[255, 135, 0], back_colour=[25, 25, 25])

        self.sense.show_message("FINISHED work order", text_colour=[0, 255, 255], back_colour=[25, 25, 25])
        self.cronometer_running = False
        thread_cronometer.join()
        return (f"The work order of {self.to_produce} blocks has finished in {self.cronometer_time:.2f} seconds , there are {self.blockApproved} approved blocks and {self.blockRejected} rejected blocks, the line process detected {self.error_production} errors, with a max vibation of {self.max_vibration}")

    def on_lab(self):
        self.conf_api_headers()
        print(self.headers)
        self.workorder_listening = True
        thread_workorders = threading.Thread(target=self.workorder_start)
        thread_workorders.start()
        return True

    def testing_start(self):
        self.cronometer_running = True
        thread_cronometer = threading.Thread(target=self.cronometer)
        thread_cronometer.start()
        self.sense.show_message("Starting work order",text_colour=[0, 255, 255], back_colour=[25, 25, 25])
        print("[bold blue]Starting work order[/bold blue] ")
        for in_production in range(1,int(self.to_produce)+1):
            self.sense.show_message(f"Block # {in_production}", text_colour=[255, 135, 0], back_colour=[25, 25, 25])
            print(f"[bold green]Block # {in_production}[/bold green]")
            
            self.sensor_running = True
            thread_sensor = threading.Thread(target=self.vibration)
            thread_sensor.start()
            #Run the production line 1
            self.testing_api_production_line()
            #self.testing_production_line()
            
            self.sensor_running = False
            thread_sensor.join()

            self.sense.show_message(f" Finished {in_production} blocks in: {self.cronometer_time:.2f} seconds",  text_colour=[255, 135, 0], back_colour=[25, 25, 25])
            print(f"[bold green]Finished {in_production} blocks in: {self.cronometer_time:.2f} seconds[/bold green]")
        self.sense.show_message("FINISHED work order", text_colour=[0, 255, 255], back_colour=[25, 25, 25])
        print(f"[bold blue]FINISHED work order[/bold blue]")
        
        self.cronometer_running = False
        thread_cronometer.join()

        self.workorder_listening = True

        self.update_work_order(state="COMPLETED")
        return (f"The work order of {self.to_produce} blocks has finished in {self.cronometer_time:.2f} seconds , there are {self.blockApproved} approved blocks and {self.blockRejected} rejected blocks, the line process detected {self.error_production} errors, with a max vibation of {self.max_vibration}")

    def testing_production_line(self):
        #Set init point
        self.block_production()
        self.block_production(arm=2)

        # #Choose block and set to graving station
    
        self.block_production('BLOCK_MOVEMENT.txt',1)

        # #Graving station
        self.block_production("LASER_MOVEMENT_START.txt",2)
        
        #agregar vibracion de sensor en el laser para que no gabre el segundo 
        if self.error_production == 0:
            self.block_production("IoT.txt",2)
            
        self.block_production("LASER_MOVEMENT_FINISH.txt",2)
        

        #Pick block and set it to quality control station
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        #Quality control
        self.block_production(arm=3)

        return True
    
    def testing_api_production_line(self):
        #Set init point
        time.sleep(1)
        time.sleep(1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")

        #Choose block and set to graving station
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        time.sleep(1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        #Graving station
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="INUSE", accelerometer=self.accelerometer)
        time.sleep(1)
        
        #check if is there an error, it would not grave the block 
        if self.error_production == 0:
            time.sleep(1)
            time.sleep(1)
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        else:
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="DOWN", accelerometer=self.accelerometer)
            time.sleep(1)
            
        #Pick block and set it to quality control station
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        time.sleep(1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        #Quality control
        print(self.quality_control())
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")