A tiny redis client for script boys with high performance.

# Install

`pip install redisio`

# Usage

**TLDR**: The following is the document but don't read it. Instead read [the code](./redisio/redisio.py). It's much shorter.

## Initialize

```python
import redisio
rd = redisio.Redis(host='127.0.0.1', port=6379, db=0, password='')
```

The arguments above are set as default so can be omitted.

Connecting via unix sockets is also available.

```python
import redisio
rd = redisio.Redis(socket='/tmp/redis.sock')
```

## Commands

See the list of Redis commands at [redis.io](https://redis.io/commands).

Since `redisio` is designed to be implemented strictly in [protocol](https://redis.io/topics/protocol) with little syntax sugar on calling but not any modification on data itself, any future commands of `redis` can be properly supported without update.

### Write I: Commands and Pipelines

Instance `redisio.Redis` is callable.

Any direct calling on it sends the commands (either single command or multiple in list) to the server and then return the client instance itself immediately without reading replies in order to be called in chain conveniently:

```python
assert rd == rd('SET', 'x', 3)('GET', 'x')(['SET', 'x', 3], ['GET', 'x'])
```

### Read I: Single Reply

Method `redisio.Redis.next` returns the first reply in the message queue from the server:

```python
assert 'OK' == rd('SET', 'x', 3)('GET', 'x').next()
assert '3' == next(rd)
```

*Note*: It will be blocked to call `next` when the queue is empty.

Reply in the queue can be reached by the index:

```python
assert '3' == rd('SET', 'x', 3)('GET', 'x')('SET', 'x', 4)[-2]
```

*Note*: It will first iterate the whole queue and then return the specific reply, with of course a side-effect to empty the queue.

Each redis command is mapped to a method with the same name.  
Calling it in this method-like way will send the command, then read all the replies, and return the last one.

```python
assert '3' == rd('SET', 'x', 3).get('x')
```

*Note*: It will be blocked to call `rd.shutdown()` because this command will never be answered (Dead Men Tell No Tales). `rd('SHUTDOWN')` should be used.

### Read II: Multiple Replies

Instance `redisio.Redis` is iterable.

So iterating it to get all the replies.

```python
r, = rd("HGET", key, field)
r1, r2= rd("HGET", key, field)("HGET", key, field2)
r1, r2= list(rd(["GET", key], ("GET", key2))(["SET", "X", "Y"]))[:2]
```


### Write II: Massive Insertion

If you want to insert a large amount of data into redis without the care of the results, you can close the connection after sending it by the use of `del` to avoid parsing the replies.

```python
rd(*large_scale_of_cmds).__del__()
```

Benefit from this the massive insertion is blazingly fast: sending a million of HSET cost only 5.355 seconds via `redisio` while it costs 23.918 seconds via `redis-py`.

*Note*: Replies are buffered on the server if the client have not read them while the connection keeps alive. This will eventually make the server crash because of the increasing occupied memory. So be aware.

`redisio` will automatically reset the connection before sending a command in the method-like way while there are more than 1024 replies to read.

```python
rd(*large_scale_of_cmds).dbsize()
rd(*large_scale_of_cmds)('DBSIZE')[-1]
```

The former is usually faster than the latter because no massive replies need to be read and parsed.

### Pub/Sub/Monitor

```python
rd.monitor()
# rd.subscribe('channel')
while 1:
    print next(rd)
```

# Q&A

Q: Why not using [redis-py](https://github.com/andymccurdy/redis-py) but redisio?  
A: To accomplish the majority of tasks [redis-py](https://github.com/andymccurdy/redis-py) is recommended and mostly used even by myself. Frankly speaking You may never need redisio. redisio is written and optimized especially for massive insertion so it is memory-saving and much faster.

Q: How to use redisio in bash?  
A: [redis-cli](https://redis.io/download) is available in bash.

Q: How to use redisio with thread safety?  
A: [redis-py](https://github.com/andymccurdy/redis-py) is thread safe.

Q: Why the result of hgetall is not a dict but a list?  
A: This is the original format of replies from redis-server. Once you get used to this original style, you will be able to process results fluently from redis-cli or [Lua Script](https://redis.io/commands/eval) without the mess of confusing types or structures brought by other brilliant libraries. Anyway let's get down to brass tacks. You can get your dict like this:

```python
hash_values = rd.hgetall('a_hash_key')
hash_dict = dict(zip(hash_values[::2], hash_values[1::2]))
```
