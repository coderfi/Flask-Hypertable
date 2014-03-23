from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hyperthrift.gen2 import HqlService

import traceback

class ThriftClient(HqlService.Client):
  def __init__(self, host, port, timeout_ms = 300000, do_open = 1):
    self.timeout_ms = timeout_ms
    socket = TSocket.TSocket(host, port)
    socket.setTimeout(timeout_ms)
    self.transport = TTransport.TFramedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    HqlService.Client.__init__(self, protocol)

    if do_open:
      self.open(timeout_ms)

  @property
  def is_active(self):
    return self.do_close == 1

  def open(self, timeout_ms):
    self.transport.open()
    self.do_close = 1

  def close(self):
    if self.do_close:
      self.transport.close()
      self.do_close = 0

  def __enter__(self):
    if not self.is_active:
      self.open(self.timeout_ms)
    return self

  def __exit__(self, type, value, traceback):
    try:
      if isinstance(value, Exception):
        raise
      else:
        return True
    finally:
        self.close()
