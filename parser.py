##
## REST Mock Framework
##
## Max Kuznetsov <max@ngti.nl> 2014
##

"""
Actions/rules parser

An action has following format:

{
  RULE
  RULE
  ...

  RESPONSE_CODE
  [HEADER HEADER VALUE]
  [HEADER ...]

  RESPONSE_BODY
}
"""

import re

class Rule(object):
    """
    Represent rule as a callable predicate
    """

    TYPE_URL = "URL"
    TYPE_METHOD = "METHOD"
    TYPE_PARAM = "PARAM"
    TYPE_BODY = "BODY"

    OP_MATCH = "match"
    OP_EQ = "eq"

    METHOD_GET = "GET"
    METHOD_POST = "POST"
    METHOD_PUT = "PUT"
    METHOD_DELETE = "DELETE"
    METHOD_HEAD = "HEAD"

    def __init__(self, type=None, op=None, method=None, data=None):
        self.type = type
        self.op = op
        self.method = method
        self.data = data
        self.param = None

    def process_url(self, req):
        if self.op == self.OP_MATCH:
            return self.data.search(req.parsed_url.path)
        else:
            return self.data == req.parsed_url.path

    def process_method(self, req):
        return req.command == self.method

    def process_body(self, req):
        if self.op == self.OP_MATCH:
            return self.data.search(req.body)
        else:
            return self.data == req.body

    def process_param(self, req):
        d = req.query_params.get(self.param, "")

        if self.op == self.OP_MATCH:
            return any([self.data.search(x) is not None for x in d])
        else:
            return any([self.data == x for x in d])

    def __call__(self, request):
        if self.type == self.TYPE_URL:
            return self.process_url(request)
        elif self.type == self.TYPE_METHOD:
            return self.process_method(request)
        elif self.type == self.TYPE_PARAM:
            return self.process_param(request)
        elif self.type == self.TYPE_BODY:
            return self.process_body(request)
        else:
            return False

    def __str__(self):
        return "<Rule type=%s, op=%s, method=%s, data=%s, param=%s>" % \
            (self.type, self.op, self.method, self.data, self.param)

class Action(object):
    """
    Represent a whole action block
    """

    def __init__(self):
        self.rules = []
        self.headers = []
        self.response_code = None
        self.response_body = ""

    def add_rule(self, rule):
        self.rules.append(rule)

    def add_header(self, header):
        self.headers.append(header)

    def __call__(self, req):
        return all([r(req) for r in self.rules])

    def __str__(self):
        return "<Action response_code=%s, response_body='%s', "\
               "rules=[%s], headers=[%s]" % \
            (self.response_code, self.response_body,
             ",".join([str(r) for r in self.rules]),
             self.headers)

def parse_rule_url(raw):
    """
    URL match|eq <VALUE>
    """

    rule = Rule(type=Rule.TYPE_URL)

    r = re.search(r"^(\w+)\s+(.+)$", raw, flags=re.U)

    if r is None:
        raise Exception("Invalid URL rule")

    op = r.group(1)
    value = r.group(2)

    if op == Rule.OP_MATCH:
        rule.op = Rule.OP_MATCH
        rule.data = re.compile(value)
    elif op == Rule.OP_EQ:
        rule.op = Rule.OP_EQ
        rule.data = value
    else:
        raise Exception("Invalid operation: %s" % op)

    return rule

def parse_rule_method(raw):
    """
    METHOD GET|POST|PUT|DELETE|HEAD
    """

    rule = Rule(type=Rule.TYPE_METHOD)

    if raw in [Rule.METHOD_GET, Rule.METHOD_POST, Rule.METHOD_HEAD,
               Rule.METHOD_PUT, Rule.METHOD_DELETE]:
        rule.method = raw
    else:
        raise Exception("Invalid METHOD: %s" % raw)

    return rule

def parse_rule_body(raw):
    """
    BODY match|eq <VALUE>
    """

    rule = Rule(type=Rule.TYPE_BODY)

    r = re.search(r"^(\w+)\s+(.+)$", raw, flags=re.U)

    if r is None:
        raise Exception("Invalid BODY rule")

    op = r.group(1)
    value = r.group(2)

    if op == Rule.OP_MATCH:
        rule.op = Rule.OP_MATCH
        rule.data = re.compile(value)
    elif op == Rule.OP_EQ:
        rule.op = Rule.OP_EQ
        rule.data = value
    else:
        raise Exception("Invalid operation: %s" % op)

    return rule

def parse_rule_param(raw):
    """
    PARAM <NAME> match|eq <VALUE>
    """

    rule = Rule(type=Rule.TYPE_PARAM)

    r = re.search(r"^([\w_-]+)\s+(\w+)\s+(.+)$", raw, flags=re.U)

    if r is None:
        raise Exception("Invalid PARAM rule")

    rule.param = r.group(1)
    op = r.group(2)
    value = r.group(3)

    if op == Rule.OP_MATCH:
        rule.op = Rule.OP_MATCH
        rule.data = re.compile(value)
    elif op == Rule.OP_EQ:
        rule.op = Rule.OP_EQ
        rule.data = value
    else:
        raise Exception("Invalid operation: %s" % op)

    return rule

def parse_rule(line):
    """
    Parse a rule line
    """

    r = re.search(r"^(\w+)\s+(.+)$", line, flags=re.U)

    if r is None:
        raise Exception("Invalid syntax")

    cmd = r.group(1)
    rest = r.group(2)

    CMDS = {"URL": parse_rule_url,
            "METHOD": parse_rule_method,
            "PARAM": parse_rule_param,
            "BODY": parse_rule_body,
            }

    return CMDS[cmd](rest)

def parse_header(line):
    """
    HEADER <NAME> <VALUE>
    """

    r = re.match(r'^\s*HEADER\s+(\S+?)\s+(\S+?)\s*$', line)

    if r is None:
        raise Exception("Invalid header syntax: %s" % str(line))

    return r.group(1), r.group(2)

def parse_actions(path):
    """
    Parse actions file and return a list of Action() instances
    """

    raw = ""

    with open(path) as f:
        raw = f.read()

    actions = []

    cur_action = None
    rules_block = True
    headers_block = False
    response = []

    lineno = 0

    for line in raw.split("\n"):
        lineno += 1
        line = line.strip()

        # Empty line
        if len(line) == 0:
            if rules_block:
                if cur_action is not None:
                    rules_block = False
                    headers_block = True
            elif headers_block:
                headers_block = False

            continue

        # Comment
        if line.startswith("#"):
            continue

        if line == "{":
            if cur_action is not None:
                raise Exception("line %d: Nested actions not allowed!" %lineno)
            else:
                cur_action = Action()
                rules_block = True
                response = []
                continue

        if line == "}":
            if cur_action is None:
                raise Exception("line %d: No action defined!" % lineno)
            else:
                cur_action.response_body = "\n".join(response)
                actions.append(cur_action)
                cur_action = None
                rules_block = True
                continue

        # Everything else must be inside action definition
        if cur_action is None:
            raise Exception("line %d: Missing action declaration" % lineno)

        if rules_block:
            try:
                cur_action.add_rule(parse_rule(line))
            except Exception as e:
                raise Exception("line %d: Unable to parse rule: %s" %
                                (lineno, str(e)))
        elif headers_block:
            # First comes the response code
            if cur_action.response_code is None:
                cur_action.response_code = int(line)
            else:
                cur_action.add_header(parse_header(line))
        else:
            response.append(line)

    return actions
