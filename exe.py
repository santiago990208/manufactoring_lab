from lab_manufactura import manufacturing_laboratory

#params or auth and id of organization Supremo
username = "iotadmin.00182"
password = "E5bc#m3VgXah"
org_id = "6BNYV2GM1F1G"

#serial port where the arms are connected, we listed with the command etc.
port_arm_airpicker= "/dev/ttyACM1"
port_arm_laser = "/dev/ttyACM0"

#urls of the api and the devices connectors
url_api = "http://iotdemo00182.cna.phx.demoservices005.iot.oraclepdemos.com/productionMonitoring/clientapi/v2/workOrders" #the q is for the query, filtering only the ones with released
url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/airpicker_Connector"
url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/laser_Connector"
url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/quality_Connector"
url_production_line = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/productionlineController"


manufactory = manufacturing_laboratory(username = username, password =password, org_id = org_id, port_arm1= "" , port_arm2 = "", url_api =url_api, url_airpicker = url_link_airpicker,url_laser =url_link_laser,url_belt =url_link_qualitycontrol, url_production_line = url_production_line)

manufactory.on_lab()