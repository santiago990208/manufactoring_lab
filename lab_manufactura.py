# Importando las librerías necesarias para la ejecución del programa
from pydexarm import Dexarm
from rich import print
#from sense_hat import SenseHat
import random
import requests
import base64
import json
import time
import threading
import datetime

# Definición de la clase principal del laboratorio de fabricación
class manufacturing_laboratory():
    # Método constructor de la clase
    def __init__(self, username = "", password ="", org_id = "6BNYV2GM1F1G", work_order_processed = "WO-410-1081",port_arm1= "" , port_arm2 = "", url_api ="", url_airpicker ="",url_laser ="",url_belt ="", url_production_line =""):
        
        # Parámetros de entrada
        self.username = username    # Nombre de usuario
        self.password = password    # Contraseña
        self.org_id = org_id        # ID de la organización
        self.port_arm1 = port_arm1  # Puerto para el brazo robótico 1
        self.port_arm2 = port_arm2  # Puerto para el brazo robótico 2
        # Enlaces de la API
        self.url_api = url_api                   # URL de la API
        self.url_airpicker = url_airpicker       # URL del airpicker
        self.url_laser = url_laser               # URL del láser
        self.url_belt = url_belt                 # URL de la cinta transportadora
        self.url_production_line = url_production_line  # URL de la línea de producción
        # Variables de configuración inicial
        self.headers = ""
        # Booleanos para activar hilos
        self.cronometer_running = False   # Cronómetro en ejecución
        self.sensor_running = False       # Sensor en ejecución
        self.workorder_listening = False  # Escucha de la orden de trabajo
        # Contadores
        self.cronometer_time = 0          # Tiempo del cronómetro
        self.error_production = 0         # Errores de producción
        self.work_order_processed = work_order_processed  # Orden de trabajo procesada
        # Reglas
        self.max_vibration = 1.5          # Máxima vibración para detectar un error, es una regla
        self.accelerometer = 0            # Acelerómetro
        #self.sense = SenseHat()           # Sensor de Hat
        # Estado e información de la orden de trabajo
        self.start_time_proccess = datetime.datetime.utcnow()  # Hora de inicio del proceso
        self.workorderId= ""              # ID de la orden de trabajo
        self.factory = ""                 # Fábrica
        self.productId = ""               # ID del producto
        self.to_produce = 0               # Cantidad a producir
        self.blockApproved = 0            # Bloques aprobados
        self.blockRejected = 0            # Bloques rechazados
 
    # Método para configurar los encabezados de la API
    def conf_api_headers(self):
        # Codificar el nombre de usuario y la contraseña
        auth_string = f"{self.username}:{self.password}"
        auth_bytes = auth_string.encode("utf-8")
        b64_auth_string = base64.b64encode(auth_bytes).decode("utf-8")

        # Definir los encabezados para las solicitudes de la API
        self.headers = {
            "Authorization": f"Basic {b64_auth_string}",  # Credenciales codificadas en base64
            "Content-Type": "application/json",           # Tipo de contenido a enviar
            "Accept": "application/json",                 # Tipo de contenido a recibir
            "X-ORACLE-IOT-ORG": self.org_id               # Identificación de la organización
        }

        return self.headers
    
    # Iniciar el cronómetro hasta que finalice la función
    def cronometer(self):
        start_time = time.perf_counter()
        
        while self.cronometer_running:
            self.cronometer_time = time.perf_counter() - start_time
            time.sleep(0.01)
    
    # Ejecutar la vibración del sensor en un nuevo hilo
    def vibration(self):
        print("Función de vibración iniciada")
        while self.sensor_running:
            self.accelerometer = 0.02 # Obtener la lectura del acelerómetro
            x = self.accelerometer["x"]  # Coordenada x
            y = self.accelerometer["y"]  # Coordenada y
            z = self.accelerometer["z"]  # Coordenada z

            self.accelerometer = max(x, y, z)  # Obtener el máximo valor de las coordenadas

            if self.accelerometer > self.max_vibration:  # Si la vibración es mayor que la máxima permitida
                self.error_production += 1
                print(self.error_production)
                self.max_vibration = self.accelerometer
                # self.sense.show_message(f"ERROR # {self.error_production}", text_colour=[255, 255, 255], back_colour=[255, 0, 0])
            else:
                print('Todo bien')
                #self.sense.clear((0,150,0)) # Verde
                
    # Método para iniciar la orden de trabajo
    def workorder_start(self):    
        # Mientras la orden de trabajo esté siendo escuchada
        while self.workorder_listening:
            # Mostrar en el sensor Hat el mensaje "START WORK ORDER"
            # self.sense.show_message("START WORK ORDER",text_colour=[0, 255, 255], back_colour=[25, 25, 25])
            try:
                # Query para buscar en la API una orden de trabajo que tenga el nombre especificado
                query = '?q={"name": { "$like":"' + str(self.work_order_processed) + '" } }'
                # Comprobar si la URL de la API está vacía
                if self.url_api == "":
                    raise ValueError("La URL no puede estar vacía.")
                # Realizar una solicitud GET a la API para obtener la orden de trabajo
                response = requests.get(self.url_api+query, headers=self.headers, verify=False)

                # Si la respuesta es exitosa (código 200)
                if response.status_code == 200:
                    # Decodificar el contenido de la respuesta en formato JSON
                    data = response.json()
                    if(data['items']):  
                        # Obtener la primera orden de trabajo encontrada
                        workorder = data['items'][0]  
                        # Registrar el tiempo de inicio del proceso
                        self.start_time_proccess  = datetime.datetime.utcnow()

                        # Convertir el tiempo de inicio planeado de la orden de trabajo de milisegundos a segundos y luego a formato datetime
                        planned_start_time = datetime.datetime.fromtimestamp(round(workorder["plannedStartTime"] / 1000))

                        # Si el tiempo de inicio del proceso es posterior al tiempo de inicio planeado
                        if self.start_time_proccess > planned_start_time:

                            # Actualizar las propiedades de la orden de trabajo
                            self.workorderId = workorder["id"]
                            self.factory = workorder["factory"]
                            self.productId = workorder["product"]
                            self.to_produce = workorder["plannedQuantity"]

                            # Si se actualiza con éxito la orden de trabajo a estado "EN PROCESO"
                            if self.update_work_order(state="IN_PROCESS"):
                                # Imprimir el número de bloques a producir
                                print(f'Orden de envío de: {self.to_produce:.0f} bloques') 
                                # Iniciar la orden de trabajo
                                self.start_workorder()
                                # Dejar de escuchar la orden de trabajo mientras se completa el proceso
                                self.workorder_listening = False  
                            else:
                                # Si hubo un error al actualizar el estado de la orden de trabajo
                                raise ValueError("Error al actualizar el estado de la orden de trabajo")
                # Esperar 10 segundos antes de la siguiente iteración
                time.sleep(10)
            except ValueError as e:
                return print("Ocurrió un error: ", e)
            except Exception as e:
                return print("Ocurrió un error al enviar la solicitud: ", e)

    # Método para actualizar el estado de la orden de trabajo
    def update_work_order(self, state="IN_PROCESS"):
        try:
            # Añadir el ID de la orden de trabajo a la URL de la API
            workerOrder_id = f"/{self.workorderId}"
            if self.url_api == "":
                raise ValueError("La URL no puede estar vacía.")
            # Si el estado es "EN PROCESO"
            if state == "IN_PROCESS":
                # Crear los datos a enviar en la solicitud
                data = {
                    "actualStartTime": int(time.time()),  # Tiempo actual en segundos
                    "state": state,                       # Estado de la orden de trabajo
                    "systemState": state,                 # Estado del sistema
                }
            # Si el estado es "COMPLETADO"
            if state == "COMPLETED":
                # Crear los datos a enviar en la solicitud
                data = {
                    "actualEndTime": int(time.time()),  # Tiempo actual en segundos
                    "state": state,                     # Estado de la orden de trabajo
                    "systemState": state,               # Estado del sistema
                }
            # Convertir los datos a formato JSON
            json_data = json.dumps(data)
            print(json_data)
            # Añadir al encabezado de la solicitud el método de sobrescritura HTTP PATCH
            self.headers.update({"X-HTTP-Method-Override": "PATCH"})
            print(self.headers)
            # Realizar una solicitud POST a la API para actualizar la orden de trabajo
            requests.post(self.url_api+workerOrder_id, headers=self.headers, data=json_data, verify=False)
            # Eliminar el último ítem del encabezado de la solicitud
            self.headers.popitem()
            if state == "COMPLETED":
                self.on_lab()

            return True
        except ValueError as e:
            print("Ocurrió un error: ", e)
            return False
        except Exception as e:
            print("Ocurrió un error al enviar la solicitud: ", e)
            return False

    # Método para la producción de bloques
    def block_production(self, gcode_path='RESET_POINT.txt', arm=1):
        # Se selecciona el brazo robótico a utilizar basándose en el parámetro "arm"
        if arm == 1:    # Si el brazo es 1
            dexarm = Dexarm(port=self.port_arm1)  # Se utiliza el puerto del brazo 1
        if arm == 2:    # Si el brazo es 2
            dexarm = Dexarm(port=self.port_arm2)  # Se utiliza el puerto del brazo 2
        if arm == 3:    # Si el brazo es 3
            dexarm = Dexarm(port=self.port_arm2)  # Se utiliza el puerto del brazo 2
            gcode_path = self.quality_control()   # Se llama al método quality_control para determinar la ruta del archivo gcode

        # Se abre el archivo gcode en modo lectura
        gcode_file = open(gcode_path, 'r')
        # Se lee el archivo línea por línea
        while True: 
            line = gcode_file.readline()  # Se lee la línea actual
            if not line:  # Si la línea está vacía, se sale del ciclo
                break
            command = line.strip() + '\r'  # Se formatea la línea leída para enviarla como comando
            dexarm._send_cmd(command)      # Se envía el comando al brazo robótico
        # Se cierra el archivo gcode
        gcode_file.close()

        return True  # Se retorna verdadero indicando que el proceso se completó exitosamente

    # Método para el control de calidad
    def quality_control(self):
        gcode_path =''  # Se inicializa la variable que contendrá la ruta del archivo gcode
        # Se verifica si no hubo errores en la producción
        if self.error_production == 0:  # Si no hubo errores
            self.blockApproved += 1     # Se incrementa el contador de bloques aprobados
            gcode_path = 'BELT_MOVEMENT_POS.txt'  # Se establece la ruta del archivo gcode para movimiento positivo en la cinta
            # Se realiza la monitorización de la API
            self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="INUSE", gravingCheck="Approved")
        else:  # Si hubo errores
            self.blockRejected += 1     # Se incrementa el contador de bloques rechazados
            gcode_path = 'BELT_MOVEMENT_NEG.txt'  # Se establece la ruta del archivo gcode para movimiento negativo en la cinta
            # Se realiza la monitorización de la API
            self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="INUSE", gravingCheck="Rejected")
        
        return gcode_path  # Se retorna la ruta del archivo gcode

    # Método para el monitoreo de la API
    def api_monitor(self, url="", machine_id="airpickerState",  status="IDLE", accelerometer = "1.0", gravingCheck=""): 
        try:
            # Comprueba si se proporcionó una URL
            if url == "":
                print("function send api")
                raise ValueError("The URL cannot be empty.")
        
            # Configura los datos a enviar dependiendo del ID de la máquina
            if machine_id == "airpickerState" or machine_id == "laserState":
                data = {
                    "id": machine_id,
                    "state":status,
                    "accelerometer":int(accelerometer),
                }
            elif machine_id == "qualityControl":
                data= {
                    "id": machine_id,
                    "state":status,
                    "gravingCheck":gravingCheck,
                }
            # Si el ID de la máquina es "productionLine", se envían datos de producción completos
            elif machine_id == "productionLine":
                data = {
                    "id": machine_id,
                    "product": self.productId, 
                    "quantity": self.blockApproved+self.blockRejected, 
                    "gravingCheck":gravingCheck,
                    "blockApproved": self.blockApproved,
                    "blockRejected": self.blockRejected,
                    "startTime":  int(self.start_time_proccess.timestamp),
                    "endTime":  int(time.time()),
                }

            # Convierte los datos a formato JSON
            json_data = json.dumps(data)
            print(json_data)
            # Envia los datos mediante un POST request a la URL proporcionada
            requests.post(url, headers=self.headers, data=json_data, verify=False)
            return True
        except ValueError as e:
            return print("An error occurred: ", e)
        except Exception as e:
            return print("An error occurred while sending the request: ", e)

    # Método que controla la línea de producción
    def production_line(self):
        # Inicia la producción de bloques y envía el estado inicial de las máquinas a la API
        self.block_production()
        self.block_production(arm=2)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")

        # Realiza el grabado y envía el estado de las máquinas a la API
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.block_production('BLOCK_MOVEMENT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        # Más grabado y envío del estado a la API
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="INUSE", accelerometer=self.accelerometer)
        self.block_production("LASER_MOVEMENT_START.txt",2)
        
        # Verifica si ocurrió algún error durante la producción
        print(self.error_production)
        if self.error_production == 0:
            self.block_production("IoT.txt",2)
            self.block_production("LASER_MOVEMENT_FINISH.txt",2)
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        else:
            print(self.max_vibration)
            self.api_monitor(url= self.url_laser, machine_id="laserState", status="DOWN", accelerometer=self.accelerometer)
            self.block_production("LASER_MOVEMENT_FINISH.txt",2)

        # Realiza el control de calidad y envía el estado de las máquinas a la API
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.block_production(arm=3)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")
        return True
    
    # Método para iniciar el laboratorio
    def on_lab(self):
        self.conf_api_headers()        # Configura los encabezados de la API
        print(self.headers)
        self.workorder_listening = True # Inicia la escucha de órdenes de trabajo
        thread_workorders = threading.Thread(target=self.workorder_start) # Inicia un nuevo hilo para escuchar órdenes de trabajo
        thread_workorders.start()
        return True

    # Método para iniciar la orden de trabajo
    def start_workorder(self):
        # Se inicia un hilo que se encargará de controlar el cronómetro
        self.cronometer_running = True
        thread_cronometer = threading.Thread(target=self.cronometer)
        thread_cronometer.start()

        # Se inicia la producción de bloques y se muestran mensajes indicando el progreso de la producción
        for in_production in range(1,int(self.to_produce)+1):
            self.sensor_running = True
            thread_sensor = threading.Thread(target=self.vibration)
            thread_sensor.start()

            # Se controla el valor del acelerómetro y se incrementa la cantidad de errores de producción si es necesario
            if in_production == 2 :
                self.accelerometer = 2
                self.error_production += 1
            else:
                self.accelerometer = 0.8

            # Se inicia la línea de producción
            self.production_line()

            # Se detiene el sensor y se muestra un mensaje indicando la cantidad de bloques producidos y el tiempo transcurrido
            self.sensor_running = False
            thread_sensor.join()

        # Se detiene el cronómetro, se actualiza la orden de trabajo a "COMPLETED" y se devuelve un mensaje indicando los detalles de la producción
        self.cronometer_running = False
        thread_cronometer.join()
        self.update_work_order(state="COMPLETED")
        return (f"The work order of {self.to_produce} blocks has finished in {self.cronometer_time:.2f} seconds , there are {self.blockApproved} approved blocks and {self.blockRejected} rejected blocks, the line process detected {self.error_production} errors, with a max vibation of {self.max_vibration}")

    # Método para probar la línea de producción
    def testing_production_line(self):
        # Inicia la producción de bloques
        self.block_production()
        self.block_production(arm=2)
        # Realiza el grabado de bloques
        self.block_production('BLOCK_MOVEMENT.txt',1)
        self.block_production("LASER_MOVEMENT_START.txt",2)

        # Si no hay errores de producción, continua con el grabado
        if self.error_production == 0:
            self.block_production("IoT.txt",2)

        # Finaliza el grabado y realiza el control de calidad
        self.block_production("LASER_MOVEMENT_FINISH.txt",2)
        self.block_production('BLOCK_MOVEMENT_TO_BELT.txt',1)
        self.block_production(arm=3)
        return True

    # Método para probar la línea de producción con la API
    def testing_api_production_line(self):
        # Inicia la producción de bloques y envía el estado de las máquinas a la API
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.api_monitor(url= self.url_laser, machine_id="laserState", status="IDLE", accelerometer=self.accelerometer)
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")

        # Realiza el grabado y envía el estado de las máquinas a la API
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")

        # Realiza el control de calidad y envía el estado de las máquinas a la API
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="INUSE")
        self.api_monitor(url= self.url_airpicker, machine_id="airpickerState", status="IDLE")
        self.api_monitor(url= self.url_belt, machine_id="qualityControl", status="IDLE", gravingCheck="")
        return True
