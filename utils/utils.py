from typing import List, Dict
from neo4j import Transaction, Result

from web3 import Web3
from web3.types import BlockData

import hexbytes

class ImportStorage:
	def __init__(self) -> None:
		self.rpc_url: str = ''
		self.blocklist: List[BlockData] = []

class Neo4JUtility:
	@staticmethod
	def clean_properties(properties: Dict[str, any]) -> Dict[str, str]:
		for key, value in properties.items():
			if type(value) == hexbytes.main.HexBytes:
				properties[key] = f"'{value.hex()}'"
			elif type(value) in [list]:
				properties[key] = value
			else:
				properties[key] = f"'{value}'"
		return properties

	@staticmethod
	def stringify_properties(properties: Dict[str, any]) -> str:
		sentence = ""
		cleaned_properties = Neo4JUtility.clean_properties(properties.copy())
		for key, value in cleaned_properties.items():
			sentence += f"{key}: {value}"
			if key != list(cleaned_properties)[-1]:
				sentence += ", "
		return sentence

	@staticmethod
	def create_node(labels: List[str], properties: Dict[str, str], alias="") -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"CREATE ({alias}{labelsstr} {{{cleaned_properties}}})\n"

	@staticmethod
	def merge_node(labels: List[str], properties, alias="") -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"MERGE ({alias}{labelsstr} {{{cleaned_properties}}})\n"

	@staticmethod
	def create_relationship(aliasfrom: str, relationship_type: str, properties: Dict[str, str], aliasto) -> str:

		cleaned_properties = Neo4JUtility.stringify_properties(properties)

		return f"CREATE ({aliasfrom})-[:{relationship_type} {{{cleaned_properties}}}]->({aliasto})\n"

	@staticmethod
	def set_labels(nodealias: str, labels: List[str]) -> str:

		labelsstr = ''.join([f":{label}" for label in labels])
		return f"SET {nodealias}{labelsstr}\n"

	@staticmethod
	def set_properties(nodealias: str, properties: Dict[str, str]) -> str:

		sentence = "SET "
		cleaned_properties = Neo4JUtility.clean_properties(properties)

		for key, value in cleaned_properties.items():
			sentence += f"{nodealias}.{key} = {value}"
			if key != list(cleaned_properties)[-1]:
				sentence += ", "

		return f"{sentence}\n"

def submit(tx: Transaction, sentence: str) -> list[Result]:
	return list(tx.run(sentence))

def import_transaction(tx: Transaction, transaction):
	"""
	Receive a web3 transaction create a cypher sentence and execute it.
	"""
	transaction = dict(transaction)

	addrfrom = Neo4JUtility.merge_node(["Address"], {"addr": transaction['from']}, "f")
	if transaction['to']:
		addrto = Neo4JUtility.merge_node(["Address"], {"addr": transaction['to']}, "t")
	else:
		addrto = Neo4JUtility.merge_node(["Address", "`Contract Creation`"], {"addr": transaction['to']}, "t")

	relation = Neo4JUtility.create_relationship("f", "INTERACTED_WITH", transaction, "t")

	return list (
		tx.run(f"{addrfrom}{addrto}{relation}")
	)

def import_block(tx: Transaction, block: BlockData):

	block = dict(block)
	if block.get("transactions"):
		block.pop("transactions")
	if block.get("withdrawals"):
		block.pop("withdrawals")

	blocksentence = Neo4JUtility.create_node(["Block"], block, "t")
	minersentence = Neo4JUtility.merge_node(["Address"], {'addr': block['miner']}, "f")
	relation = Neo4JUtility.create_relationship("f", "MINED", {}, "t")
	return list (
		tx.run(f"{blocksentence}{minersentence}{relation}")
	)

def create_contract_relation(tx: Transaction, receipt, transaction):
	contract = Neo4JUtility.merge_node(['Address'], {'addr': receipt['contractAddress']}, 'c')
	contract += Neo4JUtility.set_labels('c', ['Contract'])
	contract += Neo4JUtility.set_properties('c', {'code': transaction['input']})
	origin = Neo4JUtility.merge_node(['Address'], {'addr': transaction['from']}, 'f')
	relation = Neo4JUtility.create_relationship('f', "CREATED", {}, 'c')

	return list (
		tx.run(f"{contract}{origin}{relation}")
	)

def init_web3(rpc_url: str) -> Web3:
	print(f"Initiating a connection to {rpc_url}")
	w3 = Web3(Web3.HTTPProvider(rpc_url))
	if not w3.is_connected():
		raise BaseException("Could not connect to rpc url", w3)
	return w3
