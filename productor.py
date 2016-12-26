#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import asyncio_redis
from asyncio_redis import RedisProtocol
import asyncio
import curio

# @asyncio.coroutine
async def save(future):
	# yield from asyncio.sleep(5)
	# Create Redis connection
	connection = await asyncio_redis.Connection.create(host='localhost', port=6379)
	# Set a key
	await connection.set('my_key', '456')
	# When finished, close the connection.
	connection.close()
	future.set_result('123')

# async def save(data):
#     await curio.sleep(5)
#     connection = await asyncio_redis.Connection.create(host='localhost', port=6379)
#     await connection.set('my_key', data)
#     connection.close()

if __name__ == '__main__':
	# loop = asyncio.get_event_loop()
	# # future = asyncio.Future()
	# future = asyncio.Future()
	# asyncio.ensure_future(save(future))
	# loop.run_until_complete(future)
	# print(future.result())
	# # loop.run_forever(future)
	# loop.close()
	loop = asyncio.get_event_loop()

	def run():
		# Create connection
		transport, protocol = yield from loop.create_connection(RedisProtocol, 'localhost', 6379)

		# Set a key
		yield from protocol.set('key', 'value')

		# Retrieve a key
		result = yield from protocol.get('key')

		# Print result
		print ('Succeeded', result == 'value')

		transport.close()

	loop.run_until_complete(run())		