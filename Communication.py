from opcua import Client
from opcua import ua
#logging.basicConfig(level=logging.DEBUG)
Cpx_opc_ua_gvl_node_list={
    'MatchStarted'      :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bMatchStarted",
    'bMatchFinished'    :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bMatchFinished",
    'ErrorCode'        :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iErrorCode",
    'EmptyBoard'       :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bEmptyBoard",
    'BallDropColumn'   :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iBallDropColumn",
    'BallDropDone'     :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.bBallDropDone",
    'StateMachine'      :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.StateMachine",
    'PlayerSet'         :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.Player",
    'test'              :"ns=4;s=|var|CPX-E-CEC-C1-PN.Application.GVL_OPC_UA.iTestvariable_write"
}

#****************************************Connect the opc-ua client********************************************
opc_ua_url = "opc.tcp://192.168.0.10:4840"
print("OPC UA is running")

class UA_Client():
    def __init__(self,url):
        self.url=url
        try:
            self.client=Client(self.url)
            self.client.connect()
            print("OPC-UA connection successful")
        except Exception as e:
            print(f"OPC-UA connection not established {e}")

    def readOPC_UA_NodeValue(self, nodeID):
        refNode=self.client.get_node(nodeID)
        return refNode.get_value()

    def writeOPC_UA_NodeValue(self, nodeID, value, variableType=ua.VariantType.Int16):
        refNode=self.client.get_node(nodeID)
        return refNode.set_value(value=value,varianttype=variableType)
        #confirm if the value is written


if __name__=="__main__":
    CPXClient=UA_Client(opc_ua_url)
    CPXClient.writeOPC_UA_NodeValue(Cpx_opc_ua_gvl_node_list['test'],value=10,variableType=ua.VariantType.Int16)
