from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict


class StringEnum():

	@classmethod
	def get_list(cls) -> List[str]:
		class_attribute_names = dir(cls)
		list_of_string_attributes = []  # type: List[str]
		for class_attribute_name in class_attribute_names:
			if not class_attribute_name.startswith("__"):
				class_attribute_value = getattr(cls, class_attribute_name)
				if isinstance(class_attribute_value, str):
					list_of_string_attributes.append(class_attribute_value)
		return list_of_string_attributes


class GameServerManagerMessageTypeEnum(StringEnum):
	GameStartRequested = "game_start_requested"
	ClientStateInformation = "client_state_information"
	ServerToClientResponse = "server_response"
	GameCompleted = "game_completed"


class GameServerManagerMessage():

	def __init__(self, *, game_server_manager_message_type: str, message_json: Dict):

		self.__game_server_manager_message_type = game_server_manager_message_type
		self.__message_json = message_json

	def get_game_server_manager_message_type(self) -> str:
		return self.__game_server_manager_message_type

	def get_message_json(self) -> Dict:
		return self.__message_json


class GameServerManagerClient():

	def __init__(self, *, host_address: str, host_port: int):

		self.__host_address = host_address
		self.__host_port = host_port

	def connect(self):

		raise NotImplementedError()

	def send_message(self, *, game_server_manager_message: GameServerManagerMessage):

		raise NotImplementedError()

	def read_message(self) -> GameServerManagerMessage:

		raise NotImplementedError()


class GameServerManagerClientFactory():

	def __init__(self, *, host_address: str, host_port: int):

		self.__host_address = host_address
		self.__host_port = host_port

	def get_game_server_manager_client(self) -> GameServerManagerClient:

		return GameServerManagerClient(
			host_address=self.__host_address,
			host_port=self.__host_port
		)


class GameServerManagerServer(ABC):

	def __init__(self, *, host_address: str, host_port: int):

		self.__host_address = host_address
		self.__host_port = host_port

	@abstractmethod
	def start(self):
		raise NotImplementedError()

	@abstractmethod
	def process_message(self, *, game_server_manager_message: GameServerManagerMessage):
		raise NotImplementedError()

	@abstractmethod
	def stop(self):
		raise NotImplementedError()
