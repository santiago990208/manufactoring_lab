# Importamos la clase manufacturing_laboratory desde el archivo lab_manufactura.py
from lab_manufactura import manufacturing_laboratory

# Definimos los parámetros de autenticación y el ID de la organización Supremo
username = "iotadmin.00182"
password = "pyNX#qQxh89k"
org_id = "6KQBWCBW1F1G"
work_order_processed = "WO-410-1081"

# Definimos los puertos seriales donde están conectados los brazos robóticos.
# Usualmente los obtenemos mediante un comando en el terminal.
port_arm_airpicker= "/dev/ttyACM0"
port_arm_laser = "/dev/ttyACM1"

# Definimos las URLs de la API y los conectores de los dispositivos
url_api = "https://iotdemo00182.cna.phx.demoservices005.iot.oraclepdemos.com/productionMonitoring/clientapi/v2/workOrders" 
url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/airpickerConnector"
url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/laserConnector"
url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/qualityConnector"
url_production_line = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/productionlineController"

# Creamos un objeto de la clase manufacturing_laboratory pasándole los parámetros correspondientes
manufactory = manufacturing_laboratory(username = username, password =password, org_id = org_id, work_order_processed = work_order_processed, port_arm1= port_arm_airpicker , port_arm2 = port_arm_laser, url_api =url_api, url_airpicker = url_link_airpicker,url_laser =url_link_laser,url_belt =url_link_qualitycontrol, url_production_line = url_production_line)

# Iniciamos el laboratorio con el método on_lab()
manufactory.testing_production_line()

#LOS ARHIVOS .txt SON LO GCODE DE LOS BRAZOS Y BANDA, SE GENRARON CON LA APLICACION ROTRICS, IR A SU DOCUMENTACION PARA CONOCER MAS.