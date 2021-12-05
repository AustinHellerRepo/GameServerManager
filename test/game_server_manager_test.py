import unittest
from src.austin_heller_repo.game_server_manager import GameServerManagerMessage, GameServerManagerServer, GameServerManagerMessageTypeEnum, GameServerManagerClient
from austin_heller_repo.socket import ServerSocketFactory, ClientSocket, ClientSocketFactory
from typing import List, Tuple, Dict, Callable
import time
import json
from datetime import datetime


class TestGameServerManagerServer(GameServerManagerServer):

	def __init__(self, *, server_socket_factory: ServerSocketFactory, host_address: str, host_port: int):
		super().__init__(
			server_socket_factory=server_socket_factory,
			host_address=host_address,
			host_port=host_port
		)

		self.__is_game_completed = False

	def process_message(self, *, game_server_manager_message: GameServerManagerMessage, send_response_method: Callable[[GameServerManagerMessage], None]):

		if self.__is_game_completed:
			send_response_method(GameServerManagerMessage(
				game_server_manager_message_type=GameServerManagerMessageTypeEnum.GameCompleted,
				message_json=None
			))
		else:
			if game_server_manager_message.get_game_server_manager_message_type() == GameServerManagerMessageTypeEnum.AuthenticateClientRequest:
				send_response_method(GameServerManagerMessage(
					game_server_manager_message_type=GameServerManagerMessageTypeEnum.AuthenticateClientResponse,
					message_json=game_server_manager_message.get_message_json()
				))
			elif game_server_manager_message.get_game_server_manager_message_type() == GameServerManagerMessageTypeEnum.ClientStateInformation:
				keys = []  # type: List[str]
				values = []  # type: List
				message_json = game_server_manager_message.get_message_json()
				if message_json is None:
					self.__is_game_completed = True
					send_response_method(GameServerManagerMessage(
						game_server_manager_message_type=GameServerManagerMessageTypeEnum.GameCompleted,
						message_json=None
					))
				else:
					for key, value in message_json.items():
						keys.append(key)
						values.append(value)
					response = GameServerManagerMessage(
						game_server_manager_message_type=GameServerManagerMessageTypeEnum.ServerToClientResponse,
						message_json={
							"keys": keys,
							"values": values
						}
					)
					send_response_method(response)
			elif game_server_manager_message.get_game_server_manager_message_type() == GameServerManagerMessageTypeEnum.GameStartRequest:
				send_response_method(GameServerManagerMessage(
					game_server_manager_message_type=GameServerManagerMessageTypeEnum.GameStartResponse,
					message_json=game_server_manager_message.get_message_json()
				))
			else:
				raise NotImplementedError()


def get_test_game_server_manager_server_host_port() -> int:
	return 30755


def get_default_server_socket_factory() -> ServerSocketFactory:
	return ServerSocketFactory(
		to_client_packet_bytes_length=4096,
		listening_limit_total=10,
		accept_timeout_seconds=1.0,
		client_read_failed_delay_seconds=0.1,
		is_ssl=False
	)


def get_default_client_socket_factory() -> ClientSocketFactory:
	return ClientSocketFactory(
		to_server_packet_bytes_length=4096,
		server_read_failed_delay_seconds=0.1,
		is_ssl=False
	)


def get_default_test_game_server_manager_server() -> TestGameServerManagerServer:
	return TestGameServerManagerServer(
		server_socket_factory=get_default_server_socket_factory(),
		host_address="0.0.0.0",
		host_port=get_test_game_server_manager_server_host_port()
	)


class GameManagerTest(unittest.TestCase):

	def test_initialize(self):

		test_game_server_manager_server = get_default_test_game_server_manager_server()

		self.assertIsNotNone(test_game_server_manager_server)

	def test_client_authentication(self):

		test_game_server_manager_server = get_default_test_game_server_manager_server()

		test_game_server_manager_server.start()

		print(f"{datetime.utcnow()}: waiting before connecting to server...")
		time.sleep(1)

		client_socket = ClientSocket(
			packet_bytes_length=4096,
			read_failed_delay_seconds=0.1,
			is_ssl=False
		)

		print(f"{datetime.utcnow()}: connecting to server...")

		client_socket.connect_to_server(
			ip_address="0.0.0.0",
			port=get_test_game_server_manager_server_host_port()
		)

		print(f"{datetime.utcnow()}: connected to server.")

		expected_message_json = {
			"test": True
		}

		print(f"{datetime.utcnow()}: waiting before sending message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: sending message...")

		client_socket.write(json.dumps(GameServerManagerMessage(
			game_server_manager_message_type=GameServerManagerMessageTypeEnum.AuthenticateClientRequest,
			message_json=expected_message_json
		).to_json()))

		print(f"{datetime.utcnow()}: sent message to server.")
		print(f"{datetime.utcnow()}: waiting before reading message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: reading message...")

		response = GameServerManagerMessage.parse_from_json(
			json_string=client_socket.read()
		)

		print(f"{datetime.utcnow()}: read message from server.")

		self.assertIsNotNone(response)
		self.assertEqual(GameServerManagerMessageTypeEnum.AuthenticateClientResponse, response.get_game_server_manager_message_type())
		self.assertEqual(expected_message_json, response.get_message_json())

		print(f"{datetime.utcnow()}: waiting before stopping process...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: closing process...")

		test_game_server_manager_server.stop()
		client_socket.close(
			is_forced=False
		)

		print(f"{datetime.utcnow()}: closed process.")
		time.sleep(5)

	def test_client_data_to_server(self):

		test_game_server_manager_server = get_default_test_game_server_manager_server()

		test_game_server_manager_server.start()

		print(f"{datetime.utcnow()}: waiting before connecting to server...")
		time.sleep(1)

		client_socket = ClientSocket(
			packet_bytes_length=4096,
			read_failed_delay_seconds=0.1,
			is_ssl=False
		)

		print(f"{datetime.utcnow()}: connecting to server...")

		client_socket.connect_to_server(
			ip_address="0.0.0.0",
			port=get_test_game_server_manager_server_host_port()
		)

		print(f"{datetime.utcnow()}: connected to server.")

		input_message_json = {
			"test": True
		}
		expected_message_json = {
			"keys": [
				"test"
			],
			"values": [
				True
			]
		}

		print(f"{datetime.utcnow()}: waiting before sending message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: sending message...")

		client_socket.write(json.dumps(GameServerManagerMessage(
			game_server_manager_message_type=GameServerManagerMessageTypeEnum.ClientStateInformation,
			message_json=input_message_json
		).to_json()))

		print(f"{datetime.utcnow()}: sent message to server.")
		print(f"{datetime.utcnow()}: waiting before reading message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: reading message...")

		response = GameServerManagerMessage.parse_from_json(
			json_string=client_socket.read()
		)

		print(f"{datetime.utcnow()}: read message from server.")

		self.assertIsNotNone(response)
		self.assertEqual(GameServerManagerMessageTypeEnum.ServerToClientResponse, response.get_game_server_manager_message_type())
		self.assertEqual(expected_message_json, response.get_message_json())

		print(f"{datetime.utcnow()}: waiting before stopping process...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: closing process...")

		test_game_server_manager_server.stop()
		client_socket.close(
			is_forced=False
		)

		print(f"{datetime.utcnow()}: closed process.")

	def test_game_start(self):

		test_game_server_manager_server = get_default_test_game_server_manager_server()

		test_game_server_manager_server.start()

		print(f"{datetime.utcnow()}: waiting before connecting to server...")
		time.sleep(1)

		client_socket = ClientSocket(
			packet_bytes_length=4096,
			read_failed_delay_seconds=0.1,
			is_ssl=False
		)

		print(f"{datetime.utcnow()}: connecting to server...")

		client_socket.connect_to_server(
			ip_address="0.0.0.0",
			port=get_test_game_server_manager_server_host_port()
		)

		print(f"{datetime.utcnow()}: connected to server.")

		expected_message_json = {
			"test": True
		}

		print(f"{datetime.utcnow()}: waiting before sending message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: sending message...")

		client_socket.write(json.dumps(GameServerManagerMessage(
			game_server_manager_message_type=GameServerManagerMessageTypeEnum.GameStartRequest,
			message_json=expected_message_json
		).to_json()))

		print(f"{datetime.utcnow()}: sent message to server.")
		print(f"{datetime.utcnow()}: waiting before reading message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: reading message...")

		response = GameServerManagerMessage.parse_from_json(
			json_string=client_socket.read()
		)

		print(f"{datetime.utcnow()}: read message from server.")

		self.assertIsNotNone(response)
		self.assertEqual(GameServerManagerMessageTypeEnum.GameStartResponse, response.get_game_server_manager_message_type())
		self.assertEqual(expected_message_json, response.get_message_json())

		print(f"{datetime.utcnow()}: waiting before stopping process...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: closing process...")

		test_game_server_manager_server.stop()
		client_socket.close(
			is_forced=False
		)

		print(f"{datetime.utcnow()}: closed process.")
		time.sleep(5)

	def test_client_data_to_server_game_ends(self):

		test_game_server_manager_server = get_default_test_game_server_manager_server()

		test_game_server_manager_server.start()

		print(f"{datetime.utcnow()}: waiting before connecting to server...")
		time.sleep(1)

		client_socket = ClientSocket(
			packet_bytes_length=4096,
			read_failed_delay_seconds=0.1,
			is_ssl=False
		)

		print(f"{datetime.utcnow()}: connecting to server...")

		client_socket.connect_to_server(
			ip_address="0.0.0.0",
			port=get_test_game_server_manager_server_host_port()
		)

		print(f"{datetime.utcnow()}: connected to server.")

		input_message_json = None
		expected_message_json = None

		print(f"{datetime.utcnow()}: waiting before sending message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: sending message...")

		client_socket.write(json.dumps(GameServerManagerMessage(
			game_server_manager_message_type=GameServerManagerMessageTypeEnum.ClientStateInformation,
			message_json=input_message_json
		).to_json()))

		print(f"{datetime.utcnow()}: sent message to server.")
		print(f"{datetime.utcnow()}: waiting before reading message...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: reading message...")

		response = GameServerManagerMessage.parse_from_json(
			json_string=client_socket.read()
		)

		print(f"{datetime.utcnow()}: read message from server.")

		self.assertIsNotNone(response)
		self.assertEqual(GameServerManagerMessageTypeEnum.GameCompleted, response.get_game_server_manager_message_type())
		self.assertEqual(expected_message_json, response.get_message_json())

		print(f"{datetime.utcnow()}: waiting before stopping process...")
		time.sleep(1)
		print(f"{datetime.utcnow()}: closing process...")

		test_game_server_manager_server.stop()
		client_socket.close(
			is_forced=False
		)

		print(f"{datetime.utcnow()}: closed process.")

	def test_game_server_manager_client(self):

		game_server_manager_client = GameServerManagerClient(
			client_socket_factory=get_default_client_socket_factory(),
			host_address="0.0.0.0",
			host_port=get_test_game_server_manager_server_host_port()
		)

		self.assertIsNotNone(game_server_manager_client)

		game_server_manager_server = get_default_test_game_server_manager_server()

		game_server_manager_server.start()

		game_server_manager_client.connect()

		game_server_manager_client.send_message(
			game_server_manager_message=GameServerManagerMessage(
				game_server_manager_message_type=GameServerManagerMessageTypeEnum.GameStartRequest,
				message_json=None
			)
		)

		response = game_server_manager_client.read_message()

		self.assertEqual(GameServerManagerMessageTypeEnum.GameStartResponse, response.get_game_server_manager_message_type())

		game_server_manager_client.send_message(
			game_server_manager_message=GameServerManagerMessage(
				game_server_manager_message_type=GameServerManagerMessageTypeEnum.ClientStateInformation,
				message_json=None
			)
		)

		response = game_server_manager_client.read_message()

		self.assertEqual(GameServerManagerMessageTypeEnum.GameCompleted, response.get_game_server_manager_message_type())

		# for every message type, return completed
		for game_server_manager_message_type in list(GameServerManagerMessageTypeEnum):
			game_server_manager_client.send_message(
				game_server_manager_message=GameServerManagerMessage(
					game_server_manager_message_type=game_server_manager_message_type,
					message_json={
						"something": True
					}
				)
			)

			response = game_server_manager_client.read_message()

			self.assertEqual(GameServerManagerMessageTypeEnum.GameCompleted, response.get_game_server_manager_message_type())

		game_server_manager_client.close(
			is_forced=False
		)

		game_server_manager_server.stop()
