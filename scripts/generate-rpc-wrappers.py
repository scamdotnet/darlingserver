#!/usr/bin/env python3

import os
import sys
from collections import OrderedDict
import textwrap
from datetime import datetime

# NOTE: in Python 3.7+, we can rely on dictionaries having their items in insertion order.
#       unfortunately, we can't expect everyone building Darling to have Python 3.7+ installed.
calls = [
	('checkin', [], []),

	('checkout', [], []),

	('vchroot_path', [
		('buffer', 'char*', 'uint64_t'),
		('buffer_size', 'uint64_t'),
	], [
		('length', 'uint64_t'),
	]),

	('task_self_trap', [], [
		('port_name', 'unsigned int'),
	]),

	('mach_reply_port', [], [
		('port_name', 'unsigned int'),
	]),

	('kprintf', [
		('string', 'char*', 'uint64_t'),
		('string_length', 'uint64_t'),
	], [])
]

def parse_type(param_tuple, is_public):
	type_str = param_tuple[1].strip()
	if type_str == '@fd':
		return 'int'
	else:
		if not is_public and len(param_tuple) > 2:
			return param_tuple[2].strip()
		else:
			return type_str

def is_fd(param_tuple):
	return param_tuple[1] == '@fd'

if len(sys.argv) < 5:
	sys.exit("Usage: " + sys.argv[0] + " <public-header-path> <internal-header-path> <library-source-path> <library-import>")

os.makedirs(os.path.dirname(sys.argv[1]), exist_ok=True)
os.makedirs(os.path.dirname(sys.argv[2]), exist_ok=True)
os.makedirs(os.path.dirname(sys.argv[3]), exist_ok=True)

def to_camel_case(snake_str):
	components = snake_str.split('_')
	return ''.join(x.title() for x in components)

public_header = open(sys.argv[1], "w")
internal_header = open(sys.argv[2], "w")
library_source = open(sys.argv[3], "w")
library_import = sys.argv[4]

license_header = """\
// This file has been auto-generated by generate-rpc-wrappers.py for use with darlingserver

/**
 * This file is part of Darling.
 *
 * Copyright (C) {} Darling developers
 *
 * Darling is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Darling is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Darling.  If not, see <http://www.gnu.org/licenses/>.
 */

""".format(datetime.now().year)

public_header.write(license_header)
library_source.write(license_header)
internal_header.write(license_header)

public_header.write("""\
#ifndef _DARLINGSERVER_API_H_
#define _DARLINGSERVER_API_H_

#include <sys/types.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

""")

public_header.write("enum dserver_callnum {\n")
public_header.write("\tdserver_callnum_invalid,\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]

	public_header.write("\tdserver_callnum_" + call_name + ",\n")
public_header.write("};\n")

public_header.write("""\

typedef enum dserver_callnum dserver_callnum_t;

typedef struct dserver_rpc_callhdr {
	pid_t pid;
	pid_t tid;
	dserver_callnum_t number;
} dserver_rpc_callhdr_t;

typedef struct dserver_rpc_replyhdr {
	dserver_callnum_t number;
	int code;
} dserver_rpc_replyhdr_t;

""")

library_source.write("""\
#include {}

#if !defined(dserver_rpc_hooks_msghdr_t) || !defined(dserver_rpc_hooks_iovec_t) || !defined(dserver_rpc_hooks_cmsghdr_t) || !defined(DSERVER_RPC_HOOKS_CMSG_SPACE) || !defined(DSERVER_RPC_HOOKS_CMSG_FIRSTHDR) || !defined(DSERVER_RPC_HOOKS_SOL_SOCKET) || !defined(DSERVER_RPC_HOOKS_SCM_RIGHTS) || !defined(DSERVER_RPC_HOOKS_CMSG_LEN) || !defined(DSERVER_RPC_HOOKS_CMSG_DATA) || !defined(DSERVER_RPC_HOOKS_ATTRIBUTE)
	#error Missing definitions
#endif

#ifndef dserver_rpc_hooks_get_pid
DSERVER_RPC_HOOKS_ATTRIBUTE pid_t dserver_rpc_hooks_get_pid(void);
#endif

#ifndef dserver_rpc_hooks_get_tid
DSERVER_RPC_HOOKS_ATTRIBUTE pid_t dserver_rpc_hooks_get_tid(void);
#endif

#ifndef dserver_rpc_hooks_get_server_address
DSERVER_RPC_HOOKS_ATTRIBUTE void* dserver_rpc_hooks_get_server_address(void);
#endif

#ifndef dserver_rpc_hooks_get_server_address_length
DSERVER_RPC_HOOKS_ATTRIBUTE size_t dserver_rpc_hooks_get_server_address_length(void);
#endif

#ifndef dserver_rpc_hooks_memcpy
DSERVER_RPC_HOOKS_ATTRIBUTE void* dserver_rpc_hooks_memcpy(void* destination, const void* source, size_t length);
#endif

#ifndef dserver_rpc_hooks_send_message
DSERVER_RPC_HOOKS_ATTRIBUTE long int dserver_rpc_hooks_send_message(int socket, const dserver_rpc_hooks_msghdr_t* message);
#endif

#ifndef dserver_rpc_hooks_receive_message
DSERVER_RPC_HOOKS_ATTRIBUTE long int dserver_rpc_hooks_receive_message(int socket, dserver_rpc_hooks_msghdr_t* out_message);
#endif

#ifndef dserver_rpc_hooks_get_bad_message_status
DSERVER_RPC_HOOKS_ATTRIBUTE int dserver_rpc_hooks_get_bad_message_status(void);
#endif

#ifndef dserver_rpc_hooks_get_communication_error_status
DSERVER_RPC_HOOKS_ATTRIBUTE int dserver_rpc_hooks_get_communication_error_status(void);
#endif

#ifndef dserver_rpc_hooks_get_broken_pipe_status
DSERVER_RPC_HOOKS_ATTRIBUTE int dserver_rpc_hooks_get_broken_pipe_status(void);
#endif

#ifndef dserver_rpc_hooks_close_fd
DSERVER_RPC_HOOKS_ATTRIBUTE void dserver_rpc_hooks_close_fd(int fd);
#endif

#ifndef dserver_rpc_hooks_get_socket
DSERVER_RPC_HOOKS_ATTRIBUTE int dserver_rpc_hooks_get_socket(void);
#endif

""".format(library_import))

internal_header.write("#define DSERVER_VALID_CALLNUM_CASES \\\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]

	internal_header.write("\tcase dserver_callnum_" + call_name + ": \\\n")
internal_header.write("\n")

internal_header.write("#define DSERVER_CONSTRUCT_CASES \\\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]
	camel_name = to_camel_case(call_name)

	internal_header.write("\tCALL_CASE(" + call_name + ", " + camel_name + "); \\\n")
internal_header.write("\n")

internal_header.write("#define DSERVER_ENUM_VALUES \\\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]
	camel_name = to_camel_case(call_name)

	internal_header.write("\t" + camel_name + " = dserver_callnum_" + call_name + ", \\\n")
internal_header.write("\n")

internal_header.write("#define DSERVER_CLASS_DECLS \\\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]
	camel_name = to_camel_case(call_name)

	internal_header.write("\tclass " + camel_name + "; \\\n")
internal_header.write("\n")

internal_header.write("#define DSERVER_CLASS_DEFS \\\n")
for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]
	camel_name = to_camel_case(call_name)
	fd_count_in_reply = 0

	internal_header.write(textwrap.indent(textwrap.dedent("""\
		class Call::{1}: public Call {{ \\
			friend class Call; \\
		private: \\
			{2}
		public: \\
			{1}(MessageQueue& replyQueue, std::shared_ptr<Thread> thread, dserver_rpc_call_{0}_t* data, Message&& requestMessage): \\
				Call(replyQueue, thread, requestMessage.address()){3} \\
				{4}
			{{ \\
		"""), '\t').format(
			call_name,
			camel_name,
			("dserver_call_" + call_name + "_t _body; \\") if len(call_parameters) > 0 else "\\",
			"," if len(call_parameters) > 0 else "",
			"_body(data->body) \\" if len(call_parameters) > 0 else "\\"
		)
	)

	for param in call_parameters:
		param_name = param[0]

		if not is_fd(param):
			continue

		internal_header.write("\t\t\t_body." + param_name + " = requestMessage.extractDescriptorAtIndex(_body." + param_name + "); \\\n")
	internal_header.write("\t\t}; \\\n")

	internal_header.write("\t\t~" + camel_name + "() { \\\n")
	for param in call_parameters:
		param_name = param[0]

		if not is_fd(param):
			continue

		internal_header.write("\t\t\tif (_body." + param_name + " != -1) { \\\n")
		internal_header.write("\t\t\t\tclose(_body." + param_name + "); \\\n")
		internal_header.write("\t\t} \\\n")

	internal_header.write(textwrap.indent(textwrap.dedent("""\
			}}; \\
			virtual Call::Number number() const {{ \\
				return Call::Number::{0}; \\
			}}; \\
			virtual void processCall(); \\
		private: \\
		"""), '\t').format(camel_name))

	internal_header.write("\t\tvoid _sendReply(int resultCode")
	for param in reply_parameters:
		param_name = param[0]

		if is_fd(param):
			fd_count_in_reply += 1

		internal_header.write(", " + parse_type(param, False) + " " + param_name)
	internal_header.write(") { \\\n")

	internal_header.write(textwrap.indent(textwrap.dedent("""\
		Message reply(sizeof(dserver_rpc_reply_{0}_t), {1}); \\
		reply.setAddress(_replyAddress); \\
		auto replyStruct = reinterpret_cast<dserver_rpc_reply_{0}_t*>(reply.data().data()); \\
		replyStruct->header.number = dserver_callnum_{0}; \\
		replyStruct->header.code = resultCode; \\
		"""), '\t\t\t').format(call_name, fd_count_in_reply))

	fd_index = 0
	for param in reply_parameters:
		param_name = param[0]
		val = param_name

		if is_fd(param):
			val = str(fd_index)
			internal_header.write("\t\t\treply.pushDescriptor(" + param_name + "); \\\n")

		internal_header.write("\t\t\treplyStruct->body." + param_name + " = " + val + "; \\\n")
	internal_header.write("\t\t\t_replyQueue.push(std::move(reply)); \\\n")
	internal_header.write("\t\t}; \\\n")

	internal_header.write("\t}; \\\n")
internal_header.write("\n")

for call in calls:
	call_name = call[0]
	call_parameters = call[1]
	reply_parameters = call[2]
	fd_count_in_call = 0
	fd_count_in_reply = 0

	# define the RPC call body structure
	if len(call_parameters) > 0:
		public_header.write("typedef struct dserver_call_" + call_name + " dserver_call_" + call_name + "_t;\n")
		public_header.write("struct dserver_call_" + call_name + " {\n")
		for param in call_parameters:
			param_name = param[0]

			if is_fd(param):
				fd_count_in_call += 1

			public_header.write("\t" + parse_type(param, False) + " " + param_name + ";\n")
		public_header.write("};\n")

	# define the RPC call structure
	public_header.write(textwrap.dedent("""\
		typedef struct dserver_rpc_call_{0} dserver_rpc_call_{0}_t;
		struct dserver_rpc_call_{0} {{
			dserver_rpc_callhdr_t header;
		""").format(call_name))
	if len(call_parameters) > 0:
		public_header.write("\tdserver_call_" + call_name + "_t body;\n")
	public_header.write("};\n")

	# define the RPC reply body structure
	if len(reply_parameters) > 0:
		public_header.write("typedef struct dserver_reply_" + call_name + " dserver_reply_" + call_name + "_t;\n")
		public_header.write("struct dserver_reply_" + call_name + " {\n")
		for param in reply_parameters:
			param_name = param[0]

			if is_fd(param):
				fd_count_in_reply += 1

			public_header.write("\t" + parse_type(param, False) + " " + param_name + ";\n")
		public_header.write("};\n")

	# define the RPC reply structure
	public_header.write(textwrap.dedent("""\
		typedef struct dserver_rpc_reply_{0} dserver_rpc_reply_{0}_t;
		struct dserver_rpc_reply_{0} {{
			dserver_rpc_replyhdr_t header;
		""").format(call_name))
	if len(reply_parameters) > 0:
		public_header.write("\tdserver_reply_" + call_name + "_t body;\n")
	public_header.write("};\n")

	# declare the RPC call wrapper function
	# (and output the prototype part of the function definition)
	tmp = "int dserver_rpc_" + call_name + "("
	public_header.write(tmp)
	library_source.write(tmp)
	is_first = True
	for param in call_parameters:
		param_name = param[0]

		if is_first:
			is_first = False
			tmp = ""
		else:
			tmp = ", "
		tmp += parse_type(param, True) + " " + param_name
		public_header.write(tmp)
		library_source.write(tmp)

	for param in reply_parameters:
		param_name = param[0]

		if is_first:
			is_first = False
			tmp = ""
		else:
			tmp = ", "
		tmp += parse_type(param, True) + "* out_" + param_name
		public_header.write(tmp)
		library_source.write(tmp)
	public_header.write(");\n\n")
	library_source.write(") {\n")

	# define the RPC call wrapper function
	library_source.write(textwrap.indent(textwrap.dedent("""\
		dserver_rpc_call_{0}_t call = {{
			.header = {{
				.pid = dserver_rpc_hooks_get_pid(),
				.tid = dserver_rpc_hooks_get_tid(),
				.number = dserver_callnum_{0},
			}},
		"""), '\t').format(call_name))

	if len(call_parameters) > 0:
		library_source.write("\t\t.body = {\n")
		fd_index = 0
		for param in call_parameters:
			param_name = param[0]
			val = param_name

			if is_fd(param):
				val = "(" + param_name + " < 0) ? -1 : " + str(fd_index)
				fd_index += 1

			library_source.write("\t\t\t." + param_name + " = " + val + ",\n")
		library_source.write("\t\t},\n")

	library_source.write("\t};\n")
	library_source.write("\tdserver_rpc_reply_" + call_name + "_t reply;\n")

	if fd_count_in_call > 0 or fd_count_in_reply > 0:
		library_source.write("\tint fds[" + max(fd_count_in_call, fd_count_in_reply) + "]")
		if fd_count_in_call > 0:
			library_source.write(" = { ")
			is_first = True
			for param in call_parameters:
				param_name = param[0]

				if not is_fd(param):
					continue

				if is_first:
					is_first = False
				else:
					library_source.write(", ")
				library_source.write(param_name)
			library_source.write(" }")
		library_source.write(";\n")
		library_source.write("\tchar controlbuf[DSERVER_RPC_HOOKS_CMSG_SPACE(sizeof(fds))];\n")

	library_source.write(textwrap.indent(textwrap.dedent("""\
		dserver_rpc_hooks_iovec_t call_data = {
			.iov_base = &call,
			.iov_len = sizeof(call),
		};
		dserver_rpc_hooks_msghdr_t callmsg = {
			.msg_name = dserver_rpc_hooks_get_server_address(),
			.msg_namelen = dserver_rpc_hooks_get_server_address_length(),
			.msg_iov = &call_data,
			.msg_iovlen = 1,
		"""), '\t'))

	if fd_count_in_call == 0:
		library_source.write("\t\t.msg_control = NULL,\n")
		library_source.write("\t\t.msg_controllen = 0,\n")
	else:
		library_source.write("\t\t.msg_control = controlbuf,\n")
		library_source.write("\t\t.msg_controllen = sizeof(controlbuf),\n")

	library_source.write("\t};\n")

	if fd_count_in_call > 0:
		library_source.write(textwrap.indent(textwrap.dedent("""\
			dserver_rpc_hooks_cmsghdr_t* call_cmsg = DSERVER_RPC_HOOKS_CMSG_FIRSTHDR(&callmsg);
			call_cmsg->cmsg_level = DSERVER_RPC_HOOKS_SOL_SOCKET;
			call_cmsg->cmsg_type = DSERVER_RPC_HOOKS_SCM_RIGHTS;
			call_cmsg->cmsg_len = DSERVER_RPC_HOOKS_CMSG_LEN(sizeof(int) * {0});
			dserver_rpc_hooks_memcpy(DSERVER_RPC_HOOKS_CMSG_DATA(call_cmsg), fds, sizeof(int) * {0});
			"""), '\t').format(fd_count_in_call))

	library_source.write(textwrap.indent(textwrap.dedent("""\
		dserver_rpc_hooks_iovec_t reply_data = {
			.iov_base = &reply,
			.iov_len = sizeof(reply),
		};
		dserver_rpc_hooks_msghdr_t replymsg = {
			.msg_name = NULL,
			.msg_namelen = 0,
			.msg_iov = &reply_data,
			.msg_iovlen = 1,
		"""), '\t'))

	if fd_count_in_reply == 0:
		library_source.write("\t\t.msg_control = NULL,\n")
		library_source.write("\t\t.msg_controllen = 0,\n")
	else:
		library_source.write("\t\t.msg_control = controlbuf,\n")
		library_source.write("\t\t.msg_controllen = sizeof(controlbuf),\n")

	library_source.write("\t};\n\n")

	library_source.write("\tint socket = dserver_rpc_hooks_get_socket();\n")
	library_source.write("\tif (socket < 0) {")
	library_source.write("\t\treturn dserver_rpc_hooks_get_broken_pipe_status();\n")
	library_source.write("\t}\n\n")

	library_source.write("\tlong int long_status = dserver_rpc_hooks_send_message(socket, &callmsg);\n")
	library_source.write("\tif (long_status < 0) {\n")
	library_source.write("\t\treturn (int)long_status;\n")
	library_source.write("\t}\n\n")
	library_source.write("\tif (long_status != sizeof(call)) {\n")
	library_source.write("\t\treturn dserver_rpc_hooks_get_communication_error_status();\n")
	library_source.write("\t}\n\n")

	library_source.write("\tlong_status = dserver_rpc_hooks_receive_message(socket, &replymsg);\n")
	library_source.write("\tif (long_status < 0) {\n")
	library_source.write("\t\treturn (int)long_status;\n")
	library_source.write("\t}\n\n")
	library_source.write("\tif (long_status != sizeof(reply)) {\n")
	library_source.write("\t\treturn dserver_rpc_hooks_get_communication_error_status();\n")
	library_source.write("\t}\n\n")

	if fd_count_in_reply != 0:
		library_source.write(textwrap.indent(textwrap.dedent("""\
			dserver_rpc_hooks_cmsghdr_t* reply_cmsg = DSERVER_RPC_HOOKS_CMSG_FIRSTHDR(&replymsg);
			if (!reply_cmsg || reply_cmsg->cmsg_level != DSERVER_RPC_HOOKS_SOL_SOCKET || reply_cmsg->cmsg_type != DSERVER_RPC_HOOKS_SCM_RIGHTS || reply_cmsg->cmsg_len != DSERVER_RPC_HOOKS_CMSG_LEN(sizeof(int) * {0})) {{
				status = dserver_rpc_hooks_get_bad_message_status();
				return status;
			}}
			dserver_rpc_hooks_memcpy(fds, DSERVER_RPC_HOOKS_CMSG_DATA(reply_cmsg), sizeof(int) * {0});
			"""), '\t').format(fd_count_in_reply))

	for param in reply_parameters:
		param_name = param[0]

		if is_fd(param):
			library_source.write("\tif (out_" + param_name + ") {\n")
			library_source.write("\t\t*out_" + param_name + " = fds[reply.body." + param_name + "];\n")
			library_source.write("\t} else {\n")
			library_source.write("\t\tdserver_rpc_hooks_close_fd(fds[reply.body." + param_name + "]);\n")
			library_source.write("\t}\n")
		else:
			library_source.write("\tif (out_" + param_name + ") {\n")
			library_source.write("\t\t*out_" + param_name + " = reply.body." + param_name + ";\n")
			library_source.write("\t}\n")

	library_source.write("\treturn reply.header.code;\n")

	library_source.write("};\n\n")

public_header.write("""\
#ifdef __cplusplus
};
#endif

#endif // _DARLINGSERVER_API_H_
""")

public_header.close()
internal_header.close()
library_source.close()
