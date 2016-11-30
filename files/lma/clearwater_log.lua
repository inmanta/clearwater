-- Copyright 2015 Mirantis, Inc.
-- Copyright 2016 Inmanta NV
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
local dt     = require "date_time"
local l      = require 'lpeg'
l.locale(l)

local string = require 'string'
local patt   = require 'patterns'
local utils  = require 'lma_utils'

local msg = {
    Timestamp   = nil,
    Type        = 'log',
    Hostname    = nil,
    Payload     = nil,
    Pid         = nil,
    Fields      = nil,
    Severity    = nil,
}

-- 29-11-2016 19:39:42.195 UTC Status sip_connection_pool.cpp:447: Recycle TCP connection slot 30

ts = l.Ct(dt.date_mday * "-" * dt.date_month * "-" * dt.date_fullyear * " " * dt.time_hour * ":" * dt.time_minute * ":" * dt.time_second * dt.time_secfrac)

-- Returns the parsed datetime converted to nanosec
local timestamp = l.Cg(ts/dt.time_to_ns, "Timestamp")
local severity = l.Cg(l.P"Status" + "Warning" + "Error" + "INFO", "Severity")
local message = l.Cg(patt.Message, "Message")

-- local grammar = l.Ct(timestamp * l.space * l.P"UTC" * l.space * severity * l.space * message)
local grammar = l.Ct(timestamp * l.space * l.P"UTC"* l.space * severity * l.space * message)

function process_message ()
    local log = read_message("Payload")

    local m = grammar:match(log)
    if not m then
        return -1
    end

    m.Severity = string.upper(m.Severity)

    msg.Timestamp = m.Timestamp
    msg.Payload = m.Message
    msg.Severity = utils.label_to_severity_map[m.Severity]

    msg.Fields = {}
    msg.Fields.severity_label = m.Severity
    msg.Fields.programname = 'clearwater'
    utils.inject_tags(msg)

    return utils.safe_inject_message(msg)
end

