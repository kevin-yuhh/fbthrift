"""
PyRemote
Modeled from code formerly generated at:
  /thrift/compiler/generate/t_py_generator.cc

Used by "PyRemote" code generated by thrift_library(languages=["py",[...]])

Usage:
> functions = [...] # List of Function objects as defined by IDL
> client_class = ... # The Thrift-generated client class
> from ... import ttypes # The Thrift types for the service
> remote = RemoteClient(functions, client_class, ttypes)
> argv = sys.argv # Or you can define args programmatically
> remote.run(argv)
> # Results printed to stdout
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import itertools
import optparse
import os
import pprint
from six.moves.urllib.parse import urlparse
from six import string_types
import sys
import traceback

from thrift import Thrift
from thrift.transport import TTransport, TSocket, TSSLSocket, THttpClient
from thrift.protocol import TBinaryProtocol, TCompactProtocol, \
                            TJSONProtocol, THeaderProtocol

class Function(object):
    def __init__(self, name, return_type, args):
        self.name = name
        self.return_type = return_type
        self.args = args

class RemoteClient(object):
    """
    A controller class for a remote client. Accepts a function name and sequence
    of function arguments as positional commandline arguments. Accepts
    a set of flag options to configure how the remote call is executed.

    See `parse_args` for a list of options.

    Usage:
      remote = RemoteClient(functions, client_class, ttypes)
      remote.run(sys.argv)
    """

    usage = '%prog [OPTIONS] FUNCTION [ARGS ...]'

    def __init__(self, functions, client_class, ttypes):
        self.op = None  # OptionParser
        self.functions = functions
        self.client_class = client_class
        self.ttypes = ttypes

    def _print_functions(self, out):
        """ Print all the functions available from this service """
        out.write('Functions:\n')
        for fn_name in sorted(self.functions):
            fn = self.functions[fn_name]
            if fn.return_type is None:
                out.write('  oneway void ')
            else:
                out.write('  %s ' % (fn.return_type,))
            out.write(fn_name + '(')
            out.write(', '.join('%s %s' % (type, name)
                                for type, name, true_type in fn.args))
            out.write(')\n')

    def _exit(self, error_message=None, status=os.EX_USAGE, err_out=sys.stderr):
        """ Report an error, show help information, and exit the program """
        if error_message is not None:
            print("Error: %s" % error_message, err_out)

        if status is os.EX_USAGE:
            # Print usage info
            if self.op is not None:
                self.op.print_help(err_out)
            if self.functions is not None:
                self._print_functions(err_out)

        sys.exit(status)

    def _parse_args(self, argv):
        """ Parse commandline args into an OptionParser object """
        op = optparse.OptionParser(usage=RemoteClient.usage,
                                   add_help_option=False)
        op.disable_interspersed_args()

        op.add_option('-h', '--host',
                      action='store', metavar='HOST[:PORT]',
                      help='The host and port to connect to')
        op.add_option('-u', '--url',
                      action='store',
                      help='The URL to connect to, for HTTP transport')
        op.add_option('-f', '--framed',
                      action='store_true', default=False,
                      help='Use framed transport')
        op.add_option('-s', '--ssl',
                      action='store_true', default=False,
                      help='Use SSL socket')
        op.add_option('-U', '--unframed',
                      action='store_true', default=False,
                      help='Use unframed transport')
        op.add_option('-j', '--json',
                      action='store_true', default=False,
                      help='Use TJSONProtocol')
        op.add_option('-c', '--compact',
                      action='store_true', default=False,
                      help='Use TCompactProtocol')
        op.add_option('-t', '--tier',
                      action='store',
                      help='The SMC Tier to connect to [Not yet supported]')
        op.add_option('-?', '--help',
                      action='help',
                      help='Show this help message and exit')

        (self.options, self.args) = op.parse_args(argv[1:])
        self.op = op

    def _validate_options(self):
        """Check if there are any option inconsistencies, and exit if so"""
        if self.options.framed and self.options.unframed:
            self._exit(error_message='cannot specify both '
                       '--framed and --unframed')

        if self.options.url is not None:
            if self.options.host is not None:
                self._exit(error_message='cannot specify both '
                           '--url and --host')
            if not any([self.options.unframed, self.options.json]):
                self._exit(error_message='can only specify --url with '
                           '--unframed or --json')
        elif self.options.host is None:
            self._exit(error_message='Must specify either --url or --host')

    def _eval_arg(self, arg, thrift_types):
        """Evaluate a commandline argument within the scope of the IDL types"""
        locals().update(thrift_types)
        return eval(arg)

    def _process_fn_args(self, fn, args):
        """Proccess positional commandline args as function arguments"""
        if len(args) != len(fn.args):
            self._exit(error_message=('"%s" expects %d arguments '
                       '(received %d)') % (fn.name, len(fn.args), len(args)))

        # Get all custom Thrift types
        thrift_types = {}
        for key in dir(self.ttypes):
            thrift_types[key] = getattr(self.ttypes, key)

        fn_args = []
        for arg, arg_info in itertools.izip(args, fn.args):
            if arg_info[2] == 'string':
                # For ease-of-use, we don't eval string arguments, simply so
                # users don't have to wrap the arguments in quotes
                fn_args.append(arg)
                continue
            try:
                value = self._eval_arg(arg, thrift_types)
            except:
                traceback.print_exc(file=sys.stderr)
                self._exit(error_message='error parsing argument "%s"' % (arg,),
                           status=os.EX_DATAERR)
            fn_args.append(value)

        return fn_args

    def _process_args(self):
        """ Populate instance data using commandline arguments """
        if len(self.args) < 1:
            self._exit()
        fn_name = self.args[0]
        if fn_name not in self.functions:
            self._exit(error_message='Unknown function "%s"' % fn_name)
        else:
            self.function = self.functions[fn_name]

        self.function_args = self._process_fn_args(self.function, self.args[1:])

        self._validate_options()

    def _parse_host_port(self, value, default_port):
        parts = value.rsplit(':', 1)
        if len(parts) == 1:
            return (parts[0], default_port)
        try:
            port = int(parts[1])
        except ValueError:
            raise ValueError('invalid port: ' + parts[1])
        return (parts[0], port)

    def _execute(self):
        """
        Make the requested call.
        Assumes _parse_args() and _process_args() have already been called.
        """
        # Create the transport
        if self.options.url is not None:
            url = urlparse(self.options.url)
            host, port = self._parse_host_port(url[1], 80)
            transport = THttpClient.THttpClient(self.options.url)
        elif self.options.host is not None:
            host, port = self._parse_host_port(self.options.host, 9090)
            socket = TSSLSocket.TSSLSocket(host, port) if self.options.ssl \
                     else TSocket.TSocket(host, port)
            if self.options.framed:
                transport = TTransport.TFramedTransport(socket)
            else:
                transport = TTransport.TBufferedTransport(socket)

        # Create the protocol and client
        if self.options.json:
            protocol = TJSONProtocol.TJSONProtocol(transport)
        elif self.options.compact:
            protocol = TCompactProtocol.TCompactProtocol(transport)

        # No explicit option about protocol is specified. Try to infer.
        elif self.options.framed or self.options.unframed:
            protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)
        else:
            protocol = THeaderProtocol.THeaderProtocol(socket)
            transport = protocol.trans

        transport.open()
        client = self.client_class.Client(protocol)

        # Call the function
        method = getattr(client, self.function.name)
        try:
            ret = method(*self.function_args)
        except Thrift.TException as e:
            ret = 'Exception:\n' + str(e)

        if isinstance(ret, string_types):
            print(ret)
        else:
            pprint.pprint(ret, indent=2)

    def run(self, argv):
        self._parse_args(argv)  # Read args from commandline
        self._process_args()    # Validate and process args
        self._execute()         # Make the function call
        self._exit(status=0)