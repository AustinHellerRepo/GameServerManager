from __future__ import annotations
from austin_heller_repo.common import StringEnum
from austin_heller_repo.socket import ServerSocketFactory, ServerSocket, ClientSocket, ClientSocketFactory
from austin_heller_repo.threading import Semaphore
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Callable
import json


class GameServerManagerMessageTypeEnum(StringEnum):
	GameStartRequest = "game_start_request"
	GameStartResponse = "game_start_response"
	AuthenticateClientRequest = "authenticate_client_request"
	AuthenticateClientResponse = "authenticate_client_response"
	ClientStateInformation = "client_state_information"
	ServerToClientResponse = "server_to_client_response"
	GameCompleted = "game_completed"


class GameServerManagerMessage():

	def __init__(self, *, game_server_manager_message_type: GameServerManagerMessageTypeEnum, message_json: Dict):

		self.__game_server_manager_message_type = game_server_manager_message_type
		self.__message_json = message_json

	def get_game_server_manager_message_type(self) -> GameServerManagerMessageTypeEnum:
		return self.__game_server_manager_message_type

	def get_message_json(self) -> Dict:
		return self.__message_json

	def to_json(self) -> Dict:
		return {
			"game_server_manager_message_type": self.__game_server_manager_message_type.value,
			"message_json": self.__message_json
		}

	@staticmethod
	def parse_from_json(*, json_string: str) -> GameServerManagerMessage:
		json_object = json.loads(json_string)
		game_server_manager_message_type_value = json_object["game_server_manager_message_type"]
		message_json = json_object["message_json"]
		game_server_manager_message_type = GameServerManagerMessageTypeEnum(game_server_manager_message_type_value)
		game_server_manager_message = GameServerManagerMessage(
			game_server_manager_message_type=game_server_manager_message_type,
			message_json=message_json
		)
		return game_server_manager_message


class GameServerManagerClient():

	def __init__(self, *, client_socket_factory: ClientSocketFactory, host_address: str, host_port: int):

		self.__client_socket_factory = client_socket_factory
		self.__host_address = host_address
		self.__host_port = host_port

		self.__client_socket = None  # type: ClientSocket

	def connect(self):

		self.__client_socket = self.__client_socket_factory.get_client_socket()
		self.__client_socket.connect_to_server(
			ip_address=self.__host_address,
			port=self.__host_port
		)

	def send_message(self, *, game_server_manager_message: GameServerManagerMessage):

		game_server_manager_message_json_string = json.dumps(game_server_manager_message.to_json())
		self.__client_socket.write(game_server_manager_message_json_string)

	def read_message(self) -> GameServerManagerMessage:

		game_server_manager_message_json_string = self.__client_socket.read()
		return GameServerManagerMessage.parse_from_json(
			json_string=game_server_manager_message_json_string
		)

	def close(self, *, is_forced: bool):

		self.__client_socket.close(
			is_forced=is_forced
		)


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

	def __init__(self, *, server_socket_factory: ServerSocketFactory, host_address: str, host_port: int):

		self.__server_socket_factory = server_socket_factory
		self.__host_address = host_address
		self.__host_port = host_port

		self.__server_socket = None  # type: ServerSocket
		self.__client_sockets = []  # type: List[ClientSocket]
		self.__client_sockets_semaphore = Semaphore()
		self.__is_client_sockets_active = True

	def __on_accepted_client_method(self, client_socket: ClientSocket):

		self.__client_sockets_semaphore.acquire()
		self.__client_sockets.append(client_socket)
		self.__client_sockets_semaphore.release()

		def send_response_method(game_server_manager_message: GameServerManagerMessage):
			game_server_manager_message_json_string = json.dumps(game_server_manager_message.to_json())
			client_socket.write(game_server_manager_message_json_string)

		while self.__is_client_sockets_active:
			print(f"reading client socket...")
			try:
				game_server_manager_message_json_string = client_socket.read()
				print(f"read from client_socket: {game_server_manager_message_json_string}")
				game_server_manager_message = GameServerManagerMessage.parse_from_json(
					json_string=game_server_manager_message_json_string
				)
				try:
					self.process_message(
						game_server_manager_message=game_server_manager_message,
						send_response_method=send_response_method
					)
				except Exception as ex:
					print(f"__on_accepted_client_method: process_message: ex: {ex}")
			except Exception as ex:
				if self.__is_client_sockets_active:
					raise ex

	def start(self):

		self.__server_socket = self.__server_socket_factory.get_server_socket()
		self.__server_socket.start_accepting_clients(
			host_ip_address=self.__host_address,
			host_port=self.__host_port,
			on_accepted_client_method=self.__on_accepted_client_method
		)

	@abstractmethod
	def process_message(self, *, game_server_manager_message: GameServerManagerMessage, send_response_method: Callable[[GameServerManagerMessage], None]):
		raise NotImplementedError()

	def stop(self):

		self.__is_client_sockets_active = False
		self.__server_socket.stop_accepting_clients()
		for client_socket in self.__client_sockets:
			client_socket.close(
				is_forced=True
			)
		self.__client_sockets.clear()
		self.__server_socket.close()
