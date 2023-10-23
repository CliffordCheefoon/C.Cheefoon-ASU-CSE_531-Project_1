import grpc
from branch import branch_client_stub
from services.gprc_coms import branch_pb2_grpc
from services.gprc_coms import branch_pb2
from services.gprc_coms.branch_pb2 import branchEventRequest, branchEventResponse               # pylint: disable=no-name-in-module
from services.input_parser.parser import branch_input, event


class event_response:                                                                           # pylint: disable=invalid-name
    """Data Representation Class: Customer events"""
    def __init__(self, interface: str, result ):
        self.interface = interface
        self.result = result

class customer_response:                                                                        # pylint: disable=invalid-name
    """Data Representation Class: Customer with events"""
    def __init__(self, incoming_id : int , recv : list[event_response]):
        self.id = incoming_id
        self.recv = recv

class event_query_obj:                                                                          # pylint: disable=invalid-name
    """Data Representation Class: event"""
    def __init__(self, balance: float):
        self.balance = balance

class Customer:
    """A customer with it's own GRPC stub to it's own Branch Server"""
    events: list[event]
    def __init__(self, id: int, branch_metadata : branch_input):                                # pylint: disable=redefined-builtin
        # unique ID of the Customer
        self.id = id
        # a list of received messages used for debugging purpose
        self.recvMsg: list[event_response] = []                                                 # pylint: disable=invalid-name
        # pointer for the stub
        self.stub = self.createStub(branch_metadata)

    def soft_reset(self):
        """removes previous recv_msg without removing local branch stub, 
        use for cases were a Customer has more than one set of events to perform."""
        self.recvMsg = list()

    def createStub(self, branch_metadata : branch_input) -> branch_client_stub:                 # pylint: disable=invalid-name
        """Creates an object with the branch metadata and stub pointer"""
        channel = grpc.insecure_channel(f'localhost:{branch_metadata.port}')
        stub = branch_pb2_grpc.branchEventSenderStub(channel)
        return branch_client_stub(branch_metadata, stub)


    def executeEvents(self,events: list[event]):                                                # pylint: disable=invalid-name
        """Execute events from a customer. This is not all events for that customer, 
        just a subset that occurs at the same time"""


        for incoming_event in events:
            response: branchEventResponse = self.stub.branch_stub.MsgDelivery(
                request = branchEventRequest(
                    customer_id=self.id,
                    event_id=incoming_event.id,
                    event_type= incoming_event.interface.name,
                    money= incoming_event.money))

            if response.event_type ==  branch_pb2.event_type_enum.QUERY:                        # pylint:disable=no-member
                self.recvMsg.append(event_response("query", event_query_obj(response.balance)))

            elif response.event_type ==  branch_pb2.event_type_enum.DEPOSIT:                    # pylint:disable=no-member
                success_str : str
                if response.is_success is True:
                    success_str = "success"
                else:
                    success_str = "failed"

                self.recvMsg.append(event_response("deposit", success_str))

            elif response.event_type ==  branch_pb2.event_type_enum.WITHDRAW:                   # pylint:disable=no-member
                success_str : str
                if response.is_success is True:
                    success_str = "success"
                else:
                    success_str = "failed"

                self.recvMsg.append(event_response("withdraw", success_str))
            else:
                raise ValueError("Encountered an unexpected event_type")

    def get_customer_log(self) -> customer_response:
        "create a custom response object for output"
        return customer_response(self.id, self.recvMsg)
