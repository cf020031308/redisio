A tiny and fast redis client for script boys.

# Install

TODO: `pip install redisio`

# Usage

**WARNING**: The following is the document but don't read it. Instead read the code. It's much shorter.

## initialize

```python
import redisio
rd = redisio.Redis(
    host='127.0.0.1',
    port=6379,
    db=0,
    password=''
)
```

The arguments above are set as default so can be omitted.

## commands

See the commands list at [https://redis.io/commands] (commands).

Since `redisio` is designed to translate input and output strictly in [https://redis.io/topics/protocol] (protocol) with little syntax sugar on calling but not any modification on data itself, any future commands of `redis` can be properly supported without update.

### write I: commands and pipelines

Instance `redisio.Redis` is callable.

Any direct calling on it sends the commands (either single command or multiple in list) to server then return **itself** immediately without reading replies in order to be called in chain conveniently:

```python
assert rd == rd('SET', 'x', 3)('GET', 'x')(['SET', 'x', 3], ['GET', 'x'])
```

### read I: single reply

Method `redisio.Redis.next` returns the first reply in queue from server:

```python
assert 'OK' == rd('SET', 'x', 3).next()
assert '3' == next(rd('GET', 'x'))
```

*Note*: it will be blocked to call `next` when no reply in queue.


Or sepecific reply can be reached by index:

```python
assert '3' == rd('SET', 'x', 3)('GET', 'x')('SET', 'x', 4)[-2]
```

*Note*: it will first iterating the replies queue with a side-effect to empty it.


Each redis command is mapped to a method with a same name.  
Calling it in this method-way will return the last reply.

```python
assert '3' == rd.get('x')
```

*Note*: it may be blocked to call `rd.shutdown()` because no new reply will received after shutdown, use `rd('SHUTDOWN')` instead.

### read II: multiple replies

Instance `redisio.Redis` is iterable.

So iterating it to get all the replies.

```python
r, = rd("HGET", key, field)
r1, r2= rd("HGET", key, field)("HGET", key, field2)
r1, r2= list(rd(["GET", key], ("GET", key2))(["SET", "X", "Y"]))[:2]
```


### write II: massive insertion

If you want to insert a large amount of data into redis without the care of the results, you can close the socket after sending it to avoid parsing the replies by `del`.

```python
rd(large_scale_of_cmds).__del__()
```

TODO: performance

### pub/sub/monitor

```python
rd.monitor()
# rd.subscribe('channel')
while 1:
    print next(rd)
```

# Q & A

Q: How to use redisio in bash?  
A: Use [https://redis.io/download] (redis-cli) instead.

Q: How to be thread safe?  
A: [https://github.com/andymccurdy/redis-py] (redis-py) is thread safe.

Q: Why the result of hgetall is not a dict but a list?  
A: This is the original format or replies from redis-server. Once you get used to this original style, you will be able to process results fluently from redis-cli or [https://redis.io/commands/eval] (Lua Script) without the mess of types or structures brought by other brilliant libraries. Anyway let's get down to brass tacks, you can get your dict like this:

```python
hash_values = rd.hgetall('a_hash_key')
hash_dict = dict(zip(hash_values[::2], hash_values[1::2]))
```
