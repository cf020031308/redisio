A tiny and fast redis client for script boys.

# Install

`pip install redisio`

# Usage

**WARNING**: The following is the document but don't read it. Instead read [the code](./redisio/redisio.py). It's much shorter.

## Initialize

```python
import redisio
rd = redisio.Redis(host='127.0.0.1', port=6379, db=0, password='')
```

The arguments above are set as default so can be omitted.

Connecting to server via unix sockets is also supported.

```python
import redisio
rd = redisio.Redis(socket='/tmp/redis.sock')
```

## Commands

See the commands list at [redis.io](https://redis.io/commands).

Since `redisio` is designed to translate input and output strictly in [protocol](https://redis.io/topics/protocol) with little syntax sugar on calling but not any modification on data itself, any future commands of `redis` can be properly supported without update.

### Write I: Commands and Pipelines

Instance `redisio.Redis` is callable.

Any direct calling on it sends the commands (either single command or multiple in list) to server then return itself immediately without reading replies in order to be called in chain conveniently:

```python
assert rd == rd('SET', 'x', 3)('GET', 'x')(['SET', 'x', 3], ['GET', 'x'])
```

### Read I: Single Reply

Method `redisio.Redis.next` returns the first reply in queue from server:

```python
assert 'OK' == rd('SET', 'x', 3)('GET', 'x').next()
assert '3' == next(rd)
```

*Note*: It will be blocked to call `next` when there's no reply in queue.


A sepecific reply can be reached by index:

```python
assert '3' == rd('SET', 'x', 3)('GET', 'x')('SET', 'x', 4)[-2]
```

*Note*: It will first iterate the replies queue with a side-effect to empty it.


Each redis command is mapped to a method with a same name.  
Calling it in this method-like way will send the command, then read all the replies, and return the last one.

```python
assert '3' == rd('SET', 'x', 3).get('x')
```

*Note*: It may be blocked to call `rd.shutdown()` because no new reply will be received from server after it's shutdown. `rd('SHUTDOWN')` should be used in this situation.

### Read II: Multiple Replies

Instance `redisio.Redis` is iterable.

So iterating it to get all the replies.

```python
r, = rd("HGET", key, field)
r1, r2= rd("HGET", key, field)("HGET", key, field2)
r1, r2= list(rd(["GET", key], ("GET", key2))(["SET", "X", "Y"]))[:2]
```


### Write II: Massive Insertion

If you want to insert a large amount of data into redis without the care of the results, you can close the connection after sending it to avoid parsing the replies by the use of `del`.

```python
rd(*large_scale_of_cmds).__del__()
```

Benefit from this the massive insertion is blazingly fast: sending a million of HSET cost only 5.355 seconds via `redisio` while it costs 23.918 seconds via `redis-py`.

*Note*: Replies are buffered on server if the client does not read them but keeps connection alive. This will eventually make the server crash because of the increasing occupied memory. So be aware.

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
