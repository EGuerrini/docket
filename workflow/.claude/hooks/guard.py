#!/usr/bin/env python3
"""PreToolUse guard. Exit 2 refuses the call and shows stderr to the
model; exit 0 lets it through. Standard library, Python 3.8. One rule set for every session.

It refuses only what a malicious or injected instruction would do to the project:
- secrets: a command or code that reads, writes, copies or sources the dotenv file (naming it in a
  listing, a test, a pattern, an echo or a file's text is not a read), a Read,
  Grep or edit of it; the environment printed; a secret's variable expanded; gh's token printed; a
  recursive search for a secret's name;
- leaks: data sent to a host that is not our own (curl, wget or httpie uploads, raw sockets, ssh,
  scp, rsync, a push to another remote, code that posts); the files and git settings that send
  git, gh or curl elsewhere or run a program;
- running what was downloaded (`curl ... | sh`, a download then run);
- force pushes, deleting master, `git add` of everything;
- any typed push to master: `tools/dk/dk land <ticket>` runs the gate, then pushes (the
  guard cannot see dk's own push, which is the point).
Every refusal is logged to ~/.docket/dk/blocks.jsonl by check id (tools/dk/checks.yaml, `dk why <id>`).
Outside reads pass: WebFetch, WebSearch, a curl GET, fetch code, package installs (research is
useful). Our own hosts: .claude/guardrails.json own_hosts.
"""
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

HOME = os.path.expanduser("~")
WRAPPERS = {"command", "sudo", "time", "nohup", "nice", "exec", "env", "xargs", "timeout", "stdbuf"}
CLAUSE_WORDS = {"do", "then", "else", "elif", "{", "!"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
INTERPRETERS = {"python", "python3", "python3.8", "python3.11", "python3.12", "node", "ruby", "perl", "php"}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
GREP_LIKE = {"grep", "egrep", "fgrep", "rg", "ugrep"}
GREP_VALUE_OPTS = {"-A", "-B", "-C", "-m", "-d", "-D", "-t", "-T", "-g", "-M", "-j", "--max-count", "--context",
                   "--after-context", "--before-context", "--type", "--type-not", "--glob", "--iglob", "--include",
                   "--exclude", "--exclude-dir", "--max-columns", "--color", "--colour", "--threads", "--label"}
REFUSES = ("reading or sourcing the dotenv file", "printing secrets or the environment", "data sent to a host that is not ours",
           "running a download", "force pushes", "deleting master", "git add -A",
           "any typed push to master (use tools/dk/dk land <ticket>)")  # the SessionStart line prints these
LISTERS = {"ls", "find", "stat", "tree", "fd", "test", "["}
MENTION_ONLY = {"ls", "stat", "test", "[", "[[", "file", "du", "echo", "printf", "tree", "fd"}  # name a file, never read it
REDIRECT_TARGET_RE = re.compile(r"(?:^|[\s;&|(])\d*(?:<|>>?|&>>?)\|?\s*([^\s;&|<>()]+)")
DOTENV_RE = re.compile(r"\bload_dotenv\b|\bdotenv_values\b|\bfrom\s+dotenv\b|\bimport\s+dotenv\b|require\(\s*['\"]dotenv|['\"]dotenv/config")
MAX_COMMAND_CHARS = 100000
MAX_SEGMENTS = 2000
MAX_SPAWN_LITERALS = 2000

URL_RE = re.compile(r"(?i)\b(?:https?|ftp|wss?|ssh|git|sftp|rsync|socks4a?|socks5h?)://([^/\s'\"`?#]+)")
HOSTISH_RE = re.compile(r"(?i)^(?:[^@/\s:]+@)?([a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}|localhost|\d+\.\d+\.\d+\.\d+)(?::\d{1,5})?(?:[/:?#]|$)")
SCP_LIKE_RE = re.compile(r"^(?:[^/\s:]*@)?(\[[^\]/]+\]|[^@/\s:\[]+):(?!//)")
EXAMPLE_HOSTS = ("example.com", "example.net", "example.org", ".example", ".test", ".invalid", ".localhost")
ENV_RE = re.compile(r"(?<![\w-])\.env(?![\w-])")
ENV_BUILD_RE = re.compile(r"""\.en?['"]\s*[+,%'"]|['"]\.['"]\s*\+\s*['"]e|\bchr\(\s*46\s*\)""")
ENV_MESSAGE = "the command reads, writes or sources .env. Secrets never pass through a transcript; no session reads them."
LAND_MESSAGE = ("a push to master: pushes to master go through `tools/dk/dk land <ticket>` (it runs the gate, then "
                "pushes). Push your branch with `git push origin HEAD`.")
SECRET_NAME_RE = re.compile(r"SUPABASE|ANTHROPIC|RESEND|SERVICE_ROLE|API_KEY|SECRET|_TOKEN|PASSWORD|DATABASE_URL|PRIVATE_KEY|VERCEL_TOKEN|GH_TOKEN|GITHUB_TOKEN")
SECRET_VAR_RE = re.compile(r"\$\{?[A-Za-z0-9_]*(?:SUPABASE|ANTHROPIC|RESEND|SERVICE_ROLE|API_KEY|SECRET|TOKEN|PASSWORD|DATABASE_URL|PRIVATE_KEY)[A-Za-z0-9_]*")
REDIRECTION = re.compile(r"^\d*(>>?|<)(&\d+|\S*)$")
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n")
RUNNER_RE = re.compile(r"(?:(?<![\w.-])(?:bash|sh|zsh|dash|ksh|eval|source|exec|python[\d.]*|node|deno|bun|awk|gawk|mawk|make|xargs|perl|ruby|php|tclsh|lua)(?![\w-])|(?:^|[\s;&|(])\.\s|(?:^|[\s;&|(])\./)")
WRITE_HINT_RE = re.compile(r"""open\s*\([^,)]*,\s*(?:mode\s*=\s*)?['"][rbt]*[wax+]|mode\s*=\s*['"][rbt]*[wax+]|\bO_(?:WRONLY|RDWR|CREAT|APPEND|TRUNC)\b|write_text|write_bytes|\bshutil\.|os\.(?:rename|replace|symlink|link)|\bwriteFile|\bappendFile|\bfs\.(?:write|rename|copy|symlink)|createWriteStream|\bcopyFile""")
SPAWN_RE = re.compile(r"\bsubprocess\b|\bos\.(?:system|popen|exec\w*|spawn\w*)|\bpty\.spawn|\bchild_process\b|\bexecSync\b|\bspawnSync\b|\bexecFile|\bBun\.spawn|\bDeno\.run")
# Code that reaches the network, and code that sends data with it.
NET_CODE_RE = re.compile(r"\brequests\b|\burllib\b|\burlopen\b|\bhttpx\b|\baiohttp\b|\bhttp\.client\b|\bsocket\b|\bsmtplib\b|\bftplib\b|\bfetch\s*\(|\baxios\b|\bundici\b|\bnode-fetch\b|\bhttps?\.request\b|\bnet\.connect\b|\bXMLHttpRequest\b")
UPLOAD_CODE_RE = re.compile(r"""\.(?:post|put|patch)\s*\(|\bmethod\s*[=:]\s*['"](?:POST|PUT|PATCH|DELETE)|\b(?:data|files|json)\s*=|\bbody\s*:|\.send(?:all)?\s*\(|\bsmtplib\b|\bftplib\b""")
# git config keys that run a program or send git elsewhere.
GIT_EXEC_KEYS = {"core.hookspath", "core.sshcommand", "core.fsmonitor", "core.gitproxy", "core.pager", "core.editor",
                 "core.askpass", "sequence.editor", "credential.helper", "diff.external", "gpg.program", "gpg.ssh.program",
                 "uploadpack.packobjectshook", "http.proxy", "https.proxy", "remote.origin.proxy", "ssh.variant",
                 "protocol.allow", "protocol.ext.allow", "safe.directory"}
GIT_EXEC_PREFIXES = ("alias.", "filter.", "url.", "include.", "includeif.", "credential.")
GIT_EXEC_SUFFIXES = (".driver", ".textconv", ".command", ".cmd", ".helper", ".program", ".proxy", ".sshcommand",
                     ".url", ".pushurl", "refscommand")
GIT_ENV_RE = re.compile(r"^(?:GIT_SSH_COMMAND|GIT_SSH|GIT_CONFIG_PARAMETERS|GIT_CONFIG_COUNT|GIT_CONFIG_KEY_\d+|GIT_CONFIG_VALUE_\d+|GIT_CONFIG_GLOBAL|GIT_CONFIG_SYSTEM|GIT_CONFIG|GIT_EXEC_PATH|GIT_PAGER|GIT_ASKPASS|GIT_PROXY_COMMAND|GIT_EXTERNAL_DIFF)=")
NET_CONFIG_NAMES = (".curlrc", ".gitconfig", ".netrc", os.path.join(".config", "gh"), os.path.join(".config", "git"))
NET_CONFIG_SUFFIX_RE = re.compile(r"(?:\.curlrc|\.gitconfig|\.netrc|\.config/gh|\.config/git|\.git/config)(?![\w.-])")
NET_CONFIG_READERS = {"cat", "head", "tail", "less", "more", "grep", "rg", "ugrep", "ls", "wc", "diff", "stat", "file", "md5sum", "sha256sum", "test", "["}


def load_config(cwd):
    for root in (os.environ.get("CLAUDE_PROJECT_DIR", ""), cwd):
        path = os.path.join(root, ".claude", "guardrails.json") if root else ""
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}


def expand_home(text):
    text = re.sub(r"(?<![\w/.~-])~([A-Za-z_][\w-]*)(?=/|$|\s|['\"])", lambda m: os.path.expanduser("~" + m.group(1)), text)
    text = re.sub(r"(?:\$\{HOME\}|\$HOME\b|(?<![\w/.~-])~(?=/|$|\s))", lambda m: HOME, text)
    return re.sub(r"(?<![:/])/{2,}", "/", text)


def resolve(path, base):
    return os.path.realpath(os.path.join(base, os.path.expanduser(expand_home(path))))


# --- reading a command ------------------------------------------------------------------------

def segments(command, pipes=True):
    """Simple commands on ; && || | and newlines outside quotes."""
    out, cur, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                cur.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            cur.append(ch)
        elif ch == "\\" and i + 1 < len(command):
            cur.extend((ch, command[i + 1]))
            i += 1
        elif command.startswith("&&", i) or command.startswith("||", i):
            out.append("".join(cur))
            cur = []
            i += 1
        elif ch in (";", "\n") or (ch == "|" and pipes):
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


def words(segment):
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def tokens_of(segment):
    """The program and its arguments: subshell parentheses, assignments, wrappers and redirections off."""
    tokens = words(segment)
    if tokens and tokens[0].startswith("(") and not tokens[0].startswith("$("):
        tokens[0] = tokens[0].lstrip("(")
        tokens = tokens if tokens[0] else tokens[1:]
    if tokens and tokens[-1].endswith(")") and tokens[-1].count(")") > tokens[-1].count("("):
        tokens[-1] = tokens[-1][:-1]
        tokens = tokens if tokens[-1] else tokens[:-1]
    while tokens and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]) or tokens[0] in WRAPPERS or tokens[0] in CLAUSE_WORDS):
        tokens = tokens[2:] if tokens[0] == "timeout" and len(tokens) > 1 else tokens[1:]
    out, skip = [], False
    for t in tokens:
        if skip:
            skip = False
        elif REDIRECTION.match(t):
            skip = t.rstrip("&0123456789").endswith((">", "<"))
        else:
            out.append(t)
    return out


def git_subcommand(tokens):
    if not tokens or os.path.basename(tokens[0]) != "git":
        return None, []
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in GIT_GLOBAL_WITH_VALUE else 1
    return (tokens[i], tokens[i + 1:]) if i < len(tokens) else (None, [])


def split_heredocs(command):
    """The command with each heredoc body cut out, and the bodies with the line that feeds each."""
    bodies, out, pos = [], [], 0
    while True:
        m = HEREDOC_RE.search(command, pos)
        if not m:
            out.append(command[pos:])
            break
        head = command[command.rfind("\n", 0, m.start()) + 1:m.end() - 1]
        end = re.compile(r"^\s*%s\s*$" % re.escape(m.group(2)), re.M).search(command, m.end())
        out.append(command[pos:m.end()])
        bodies.append((head, command[m.end():end.start() if end else len(command)]))
        pos = end.end() if end else len(command)
    return "".join(out), bodies


def heredoc_feeder(line):
    """'shell', an interpreter's name, or None (the body is data)."""
    kind = None
    for seg in segments(line):
        toks = tokens_of(seg)
        n = os.path.basename(toks[0]) if toks else ""
        if n in SHELLS:
            return "shell"
        if n in INTERPRETERS or n.startswith("python3"):
            kind = kind or n
    return kind


def written_to_file(line):
    """The heredoc line writes its body to files (`cat > x.ts <<EOF`, `tee x`), none of them a secrets file."""
    targets = re.findall(r"(?:\d*>>?\|?\s*|\btee\s+(?:-a\s+)?)([^\s;&|<>]+)", line)
    return bool(targets) and not any(secrets_file(x.strip("'\"")) for x in targets)


def heredoc_is_text(line):
    """A body that is prose: a commit's message or a docs file (.md, .txt)."""
    if any(git_subcommand(tokens_of(seg))[0] == "commit" for seg in segments(line)):
        return True
    targets = re.findall(r"(?:\d*>>?\|?\s*|\btee\s+(?:-a\s+)?)([^\s;&|<>]+)", line)
    return bool(targets) and all(t.strip("'\"").endswith((".md", ".txt")) for t in targets)


def substitutions(command):
    """The bodies of $( ) and backtick substitutions outside single quotes, outermost first."""
    out, i, quote = [], 0, None
    while i < len(command):
        ch = command[i]
        if quote == "'":
            quote = None if ch == "'" else quote
        elif ch == "\\":
            i += 1
        elif ch == "'" and quote is None:
            quote = "'"
        elif ch == '"':
            quote = None if quote == '"' else '"'
        elif command.startswith("$(", i) and not command.startswith("$((", i):
            depth, j = 1, i + 2
            while j < len(command) and depth:
                if command[j] == "\\":
                    j += 1
                else:
                    depth += {"(": 1, ")": -1}.get(command[j], 0)
                j += 1
            out.append(command[i + 2:j - 1] if not depth else command[i + 2:])
            i = j
            continue
        elif ch == "`":
            j = i + 1
            while j < len(command) and command[j] != "`":
                j += 2 if command[j] == "\\" else 1
            out.append(command[i + 1:j])
            i = j + 1
            continue
        i += 1
    return out


# --- secrets ----------------------------------------------------------------------------------

def env_named(text):
    return any(not text[m.end():].startswith(".example") for m in ENV_RE.finditer(text))


def grep_pattern(ws, start):
    """Indexes of a grep's pattern words (the first operand, or every -e value)."""
    drop, given, j, operands = set(), False, start, False
    while j < len(ws):
        w = ws[j]
        if not operands and w == "--":
            operands = True
        elif not operands and w in ("-e", "--regexp"):
            drop.add(j + 1)
            given = True
            j += 1
        elif not operands and (w.startswith("--regexp=") or (w.startswith("-e") and len(w) > 2 and not w.startswith("--"))):
            drop.add(j)
            given = True
        elif not operands and (w in ("-f", "--file") or w in GREP_VALUE_OPTS):
            j += 1
        elif not operands and w.startswith("-") and w != "-":
            pass
        elif not given:
            drop.add(j)
            given = True
        j += 1
    return drop


def env_text(segment):
    """The segment less the words that are text, not a read: a grep's pattern and a commit's message."""
    ws = words(segment)
    i = 0
    while i < len(ws) and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", ws[i]) or ws[i] in WRAPPERS or ws[i] in CLAUSE_WORDS):
        i += 1
    if i >= len(ws):
        return segment
    name, drop = os.path.basename(ws[i].lstrip("(")), set()
    if name == "git":
        sub, args = git_subcommand(ws[i:])
        at = len(ws) - len(args)
        if sub == "commit":
            for j in range(at, len(ws)):
                if ws[j - 1] in ("-m", "--message") or (ws[j].startswith("-m") and len(ws[j]) > 2) or ws[j].startswith("--message="):
                    drop.add(j)
        elif sub == "grep":
            drop = grep_pattern(ws, at)
    elif name in GREP_LIKE:
        drop = grep_pattern(ws, i + 1)
    return " ".join(w for k, w in enumerate(ws) if k not in drop or "$(" in w or "`" in w)


def mentions_only(toks):
    """A command that names a file without reading it: an existence test, a listing, an echo. Naming the
    secrets file is not reading it: the rule was narrowed in October 2026 after 68 of 68 refusals in two weeks were such names."""
    name = os.path.basename(toks[0]) if toks else ""
    if name == "find":
        return not any(t in ("-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fls") for t in toks)
    return name in MENTION_ONLY or git_subcommand(toks)[0] in ("check-ignore", "status", "ls-files")


def check_env_read(command):
    for pipeline in segments(command, pipes=False):
        listed = False  # `ls -a | grep '^\.env'` is an existence check: the pattern counts then
        for segment in segments(pipeline):
            for target in REDIRECT_TARGET_RE.findall(segment):  # `< .env`, `> .env`: a read or a write
                if secrets_file(target.strip("'\"")):
                    return ENV_MESSAGE
            toks = tokens_of(segment)
            if not mentions_only(toks):
                text = env_text(segment)
                if env_named(text) or (listed and env_named(segment)):
                    return ENV_MESSAGE
                for word in text.split():  # a glob the shell expands to .env: `.e*`, `.en[v]`
                    base = os.path.basename(word.strip("'\"<>"))
                    if base.startswith(".") and set(base) & set("*?[") and fnmatch.fnmatchcase(".env", base):
                        return ENV_MESSAGE
            listed = listed or (toks and os.path.basename(toks[0]) in LISTERS) or git_subcommand(toks)[0] == "ls-files"
    return None


def code_reads_env(code):
    """Code that reads the secrets file: a string literal that is its path, dotenv, or a name built to dodge the
    check. A regex or a sentence that mentions the name is not a read."""
    if ENV_BUILD_RE.search(code) or DOTENV_RE.search(code):
        return True
    for a, b, c in re.findall(r"""'([^'\n]*)'|"([^"\n]*)"|`([^`]*)`""", code):
        literal = (a or b or c).strip()
        if literal and not re.search(r"\s", literal) and secrets_file(re.sub(r"\$?\{[^}]*\}", "", literal)):
            return True  # a path literal; prose that mentions the name is not one (a spawned command is re-read)
    return False


def check_secrets(command):
    if re.search(r"""GIT_TRACE_REDACT\s*=\s*['"]?(?:0|false|no|off)\b""", command, re.I):
        return "GIT_TRACE_REDACT=0 prints git's credentials: secrets never pass through a transcript."
    m = SECRET_VAR_RE.search(command)
    if m:
        return "the command expands %s, a secret's name: secrets never pass through a transcript." % m.group(0)
    return None


def check_segment_secrets(segment, tokens):
    raw = words(segment)
    first = os.path.basename(raw[0]) if raw else ""
    if first == "printenv" or (first == "env" and all(re.match(r"^[A-Za-z_]\w*=|^-", t) for t in raw[1:])) \
            or (first in ("export", "declare", "typeset") and (len(raw) == 1 or raw[1] in ("-p", "-x", "-px"))) or raw == ["set"]:
        return "the command prints the environment, where a secret may be."
    name = os.path.basename(tokens[0]) if tokens else ""
    if name not in GREP_LIKE:
        return None
    flags = [t for t in tokens[1:] if t.startswith("-")]
    if not (name == "rg" or any(f in ("--recursive", "--dereference-recursive") or re.fullmatch(r"-[a-zA-Z]*[rR][a-zA-Z]*", f) for f in flags)):
        return None
    at = grep_pattern(tokens, 1)
    pattern = " ".join(tokens[k] for k in at)
    if not SECRET_NAME_RE.search(pattern.upper()):
        return None
    operands = [w for k, w in enumerate(tokens[1:], 1) if k not in at and not w.startswith("-")]
    if operands and all(re.search(r"\.[A-Za-z0-9]{1,5}$", os.path.basename(o)) and not os.path.basename(o).startswith(".") for o in operands):
        return None  # named files, not a tree
    return "a recursive search for a secret's name (%s) would print a line of any secrets file it meets. Search named files." % pattern


# --- hosts and leaks --------------------------------------------------------------------------

def own_host(host, config):
    host = host.lower().split("@")[-1]
    host = host.split("]")[0] + "]" if host.startswith("[") else host.split(":")[0]
    host = host.rstrip(".,;)'\"")
    if not host or "$" in host or "`" in host:
        return False
    if any(host == e.lstrip(".") or host.endswith(e if e.startswith(".") else "." + e) for e in EXAMPLE_HOSTS):
        return True
    for a in config.get("own_hosts", []):
        a = a.lower()
        if "*" in a:
            if re.fullmatch("[a-z0-9-]+".join(re.escape(p) for p in a.split("*")), host):
                return True
        elif host == a or host.endswith("." + a):
            return True
    return False


def targets_of(args, cwd):
    """The hosts a network command's words name: URLs, host:path, user@host, bare host names (a word
    that is an existing file is a file)."""
    out = []
    for a in args:
        if a.startswith("-") or a.startswith("@"):
            continue
        m = URL_RE.search(a)
        if m:
            out.append(m.group(1))
        elif "$" in a or "`" in a:
            out.append(a)  # computed: unknowable here
        elif not os.path.exists(os.path.join(cwd, a)):
            m = SCP_LIKE_RE.match(a) or HOSTISH_RE.match(a)
            if m:
                out.append(m.group(1))
    return out


CURL_UPLOAD_LONG = ("--data", "--form", "--upload-file", "--json", "--config", "--post301", "--post302", "--post303")
CURL_VALUE_SHORT = set("AbcCdDeEFHKmoPQrTtuUwxXyYz")


def network_upload(tokens, cwd):
    """For a command that sends data (a curl or wget with a body, httpie with fields, a raw socket,
    ssh, scp, rsync): the words naming where it goes, else None."""
    name = os.path.basename(tokens[0])
    args = tokens[1:]
    upload = False
    if name == "curl":
        for k, t in enumerate(args):
            if t.startswith("--"):
                opt, _, val = t.partition("=")
                if opt.startswith(CURL_UPLOAD_LONG):
                    upload = True
                elif opt == "--request":
                    method = val or (args[k + 1] if k + 1 < len(args) else "")
                    upload = upload or method.upper() not in ("GET", "HEAD")
            elif t.startswith("-") and len(t) > 1:
                for j, ch in enumerate(t[1:], 1):
                    if ch in "dFTK":
                        upload = True
                    if ch == "X":
                        method = t[j + 1:] or (args[k + 1] if k + 1 < len(args) else "")
                        upload = upload or method.upper() not in ("GET", "HEAD")
                    if ch in CURL_VALUE_SHORT:
                        break
    elif name == "wget":
        upload = any(t.startswith(("--post-", "--body-")) or (t.startswith("--method") and not re.search(r"(?i)=(?:GET|HEAD)$", t)) for t in args)
    elif name in ("http", "https", "httpie", "xh", "xhs"):
        upload = any(t.upper() in ("POST", "PUT", "PATCH", "DELETE") or t in ("-f", "--form") or t.startswith("@")
                     or re.match(r"^[\w.-]+(?::=|=|==|@|:=@)", t) and not URL_RE.search(t) for t in args)
    elif name in ("nc", "ncat", "netcat", "socat", "telnet", "ssh", "scp", "sftp", "rsync"):
        upload = True
    return targets_of(args, cwd) if upload else None


def check_upload(tokens, cwd, config):
    name = os.path.basename(tokens[0])
    where = network_upload(tokens, cwd)
    if where is None:
        return None
    if not where and name in ("rsync", "scp"):
        return None  # a local copy
    bad = [h for h in where if not own_host(h, config)] or (["(no host the guard can read)"] if not where else [])
    if bad:
        return "%s sends data to %s, which is not one of our own services. Outside reads are fine; nothing of ours is sent out." % (name, bad[0])
    return None


def check_code(code, lang, cwd, config, depth):
    """Code given to an interpreter (a heredoc body, a -c or -e argument)."""
    if code_reads_env(code):
        return ENV_MESSAGE
    if WRITE_HINT_RE.search(code):
        m = NET_CONFIG_SUFFIX_RE.search(code)
        if m:
            return "code that writes files and names %s, which sets where curl, git or gh connect or holds their credentials." % m.group(0)
    if NET_CODE_RE.search(code) and UPLOAD_CODE_RE.search(code):
        hosts = [m.group(1) for m in URL_RE.finditer(code)]
        if not hosts or not all(own_host(h, config) for h in hosts):
            return "%s code that sends data over the network to %s. Outside reads are fine; nothing of ours is sent out." % (lang, next((h for h in hosts if not own_host(h, config)), "a host the guard cannot read"))
    if SPAWN_RE.search(code) and depth < 3:
        literals = list(dict.fromkeys(a or b or c for a, b, c in re.findall(r"""'([^'\\\n]*)'|"([^"\\\n]*)"|`([^`\\]*)`""", code)))
        if len(literals) > MAX_SPAWN_LITERALS:
            return "code that starts processes and holds over %d string literals: too many to check. Put the data in a file." % MAX_SPAWN_LITERALS
        for text in literals + [" ".join(literals)]:
            reason = check_bash(text, cwd, config, depth + 1)
            if reason:
                return "a process started from code: " + reason
    return None


def check_curl_pipes(command):
    """A fetch piped or substituted into a shell or an interpreter runs what it fetched."""
    runners = SHELLS | INTERPRETERS | {"eval", "source", "."}
    for pipeline in segments(command, pipes=False):
        fetched = False
        for seg in segments(pipeline):
            toks = tokens_of(seg)
            n = os.path.basename(toks[0]) if toks else ""
            if fetched and (n in runners or n.startswith("python")):
                return "a download piped into %s runs what it fetched. Download, read it, then decide." % n
            fetched = fetched or n in ("curl", "wget")
    if re.search(r"(?:<\(|\$\(|`)\s*(?:curl|wget)\b", command) and \
            re.search(r"(?:^|[\s;&|(])(?:bash|sh|zsh|dash|eval|source|\.|python[\d.]*|node|perl|ruby)(?=\s)", command):
        return "a download substituted into a shell or an interpreter runs what it fetched."
    return None


# --- git, gh and the network's config ---------------------------------------------------------

def check_git_config(tokens):
    sub, args = git_subcommand(tokens)
    for i, t in enumerate(tokens[1:], 1):
        if t.startswith("--exec-path="):
            return "git --exec-path= runs git's commands from another directory."
        value = tokens[i + 1] if t in ("-c", "--config", "--config-env") and i + 1 < len(tokens) else \
            t.split("=", 1)[1] if t.startswith(("--config=", "--config-env=")) else None
        if value is None:
            continue
        key = value.split("=", 1)[0].strip().lower()
        if t.startswith("--config-env") or key in GIT_EXEC_KEYS or key.startswith(GIT_EXEC_PREFIXES) or key.endswith(GIT_EXEC_SUFFIXES):
            return "git %s %s runs a program or sends git elsewhere." % (t.split("=")[0], key)
    if sub == "config" and not any(a in ("--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l", "--show-origin", "get", "list") for a in args):
        keys = [a.lower() for a in args if not a.startswith("-") and a not in ("set", "unset")]
        if keys and (keys[0] in GIT_EXEC_KEYS or keys[0].startswith(GIT_EXEC_PREFIXES) or keys[0].endswith(GIT_EXEC_SUFFIXES)
                     or re.search(r"proxy|insteadof|credential|sshcommand|hookspath|askpass", keys[0])):
            return "git config %s changes where git connects or runs a program." % keys[0]
    return None


def check_git_env(segment):
    raw = words(segment)
    if raw[:1] == ["export"]:
        hit = next((w for w in raw[1:] if GIT_ENV_RE.match(w)), None)
        return "exporting %s makes git run a program or read another config." % hit.split("=")[0] if hit else None
    prefix = []
    for w in raw:
        if re.match(r"^[A-Za-z_]\w*=", w) or w in WRAPPERS:
            prefix.append(w)
            continue
        if os.path.basename(w) == "git":
            hit = next((p for p in prefix if GIT_ENV_RE.match(p)), None)
            if hit:
                return "%s on git makes it run a program or read another config." % hit.split("=")[0]
        break
    return None


def check_gh(tokens):
    if tokens[1:3] == ["auth", "git-credential"] or tokens[1:3] == ["auth", "token"] or \
            (tokens[1:3] == ["auth", "status"] and ("-t" in tokens or "--show-token" in tokens)):
        return "the command prints the GitHub token: secrets never pass through a transcript."
    return None


def net_config_path(full):
    for name in NET_CONFIG_NAMES:
        d = os.path.realpath(os.path.join(HOME, name))
        if full == d or full.startswith(d + os.sep):
            return "~/" + name
    return ".git/config" if full.endswith(os.sep + os.path.join(".git", "config")) else None


def check_net_config_write(segment, tokens, run_dir):
    """A write to ~/.curlrc, ~/.gitconfig, ~/.netrc, ~/.config/gh or git, or .git/config; a read passes."""
    name = os.path.basename(tokens[0]) if tokens else ""
    raw = words(segment)
    for k, w in enumerate(raw):
        redirected = bool(re.match(r"^\d*(?:>>?|<>|&>)", w)) or (k > 0 and re.fullmatch(r"\d*(?:>>?\|?|<>|&>>?)", raw[k - 1]) is not None)
        word = re.sub(r"^-o(?=.)", "", re.sub(r"^-{1,2}[\w-]*=", "", re.sub(r"^\d*(?:>>?\|?|<>|&>>?)", "", w)))
        if not word:
            continue
        hit = None
        if ("$" in word or "`" in word) and NET_CONFIG_SUFFIX_RE.search(word):
            hit = word
        elif "/" in word or word.startswith(".") or "~" in word:
            hit = net_config_path(resolve(word, run_dir))
        if hit and (redirected or name not in NET_CONFIG_READERS):
            return "the command writes %s, which sets where curl, git or gh connect or holds their credentials. Reading it is fine." % hit
    return None


def current_branch(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:  # noqa: B902
        return ""


def check_push(args, repo_dir, config):
    protected = config.get("protected_branches", ["master"])
    flags = [a for a in args if a.startswith("-")]
    positional = [a for a in args if not a.startswith("-")]
    if any(a == "--repo" or a.startswith("--repo=") for a in args):
        return "git push --repo names another remote. Push only to origin."
    if positional and positional[0] != "origin":
        hosts = targets_of(positional[:1], repo_dir)
        if not hosts or not all(own_host(h, config) for h in hosts):
            return "git push to %s, not origin. Push only to origin." % positional[0]
    if "--all" in flags or "--mirror" in flags:
        return "pushing every branch. Push your branch."
    refspecs = positional[1:]
    branch = current_branch(repo_dir)
    if ("--delete" in flags or "-d" in flags) and any(r.replace("refs/heads/", "") in protected for r in refspecs):
        return "deleting %s." % protected[0]
    dsts, landing = [], []
    for r in refspecs or [branch]:
        if r.startswith("+"):
            return "a force push (a +refspec)."
        src, _, dst = r.partition(":") if ":" in r else (r, "", r)
        dst = (dst.replace("refs/heads/", "") if dst != "HEAD" else branch)
        if not src and dst in protected:
            return "deleting %s." % dst
        dsts.append(dst)
        if dst in protected:
            landing.append(src)
    for flag in flags:
        if flag.startswith("--force-with-lease") or flag == "--force-if-includes":
            if any(d in protected for d in dsts):
                return "a force push to %s. Rebase on origin/%s and push again." % (protected[0], protected[0])
        elif flag in ("--force", "-f") or (re.fullmatch(r"-[a-zA-Z]+", flag) and "f" in flag):
            return "a force push. On your own branch use --force-with-lease."
    if landing:
        return LAND_MESSAGE
    return None


# --- the Bash tool ----------------------------------------------------------------------------

def check_bash(command, cwd, config, depth=0):
    command, bodies = split_heredocs(command)
    reason = check_env_read(command)
    if reason:
        return reason
    written = {}  # files this command writes (a heredoc's body, or None for a download)
    for line, body in bodies:
        feeder = heredoc_feeder(line)
        for t in re.findall(r"(?:\d*>>?\|?\s*|\btee\s+(?:-a\s+)?)([^\s;&|<>]+)", line):
            written[os.path.basename(t.strip("'\""))] = body
        if feeder == "shell":
            reason = check_bash(body, cwd, config, depth + 1) if depth < 3 else None
        elif feeder:
            reason = check_code(body, feeder, cwd, config, depth)
        elif env_named(body) and not heredoc_is_text(line) and not written_to_file(line):
            reason = ENV_MESSAGE  # data fed to a command (`xargs cat <<EOF`); data written to a file is not a read
        if reason:
            return reason
    if len(command) > MAX_COMMAND_CHARS or len(segments(command)) > MAX_SEGMENTS:
        return "the command is too long for the guard to read in its time. Write the data to a file, then run a short command on it."
    flat = " ".join(" ".join(words(seg)) for seg in segments(command))  # `cu''rl` is curl
    reason = check_secrets(command) or check_secrets(flat) or check_curl_pipes(command)
    if reason:
        return reason
    if re.search(r"/dev/(?:tcp|udp)/", command):
        return "a /dev/tcp or /dev/udp path opens a raw network socket from bash."
    if bodies and RUNNER_RE.search(command):  # a file written here may be run here: judge it as code
        for line, body in bodies:
            if not heredoc_feeder(line):
                reason = (check_bash(body, cwd, config, depth + 1) if depth < 3 else None) or check_code(body, "python3", cwd, config, depth)
                if reason:
                    return "the command writes a file and runs a program, and the file would be refused: " + reason
    if depth >= 4 and substitutions(command):
        return "the command nests $( ) or backticks deeper than the guard reads (4 levels). Flatten it."
    for body in substitutions(command) if depth < 4 else []:
        reason = check_bash(body, cwd, config, depth + 1)
        if reason:
            return reason
    for segment in segments(command):  # what a download writes is never run by the same command
        toks = tokens_of(segment)
        if toks and os.path.basename(toks[0]) in ("curl", "wget"):
            for k, t in enumerate(toks):
                m = re.match(r"^(?:--output=|--output-document=|-O(?=.)|-[a-zA-Z]*o(?=.))(.+)$", t)
                if m:
                    written[os.path.basename(m.group(1))] = None
                elif (t in ("-o", "--output", "-O", "--output-document") or re.fullmatch(r"-[a-zA-Z]*o", t)) and k + 1 < len(toks):
                    written[os.path.basename(toks[k + 1])] = None
                elif URL_RE.search(t) and os.path.basename(toks[0]) == "wget":
                    written[os.path.basename(t.rstrip("/").split("?")[0])] = None
    run_dir = cwd
    for segment in segments(command):
        tokens = tokens_of(segment)
        reason = check_segment_secrets(segment, tokens) or check_git_env(segment) or check_net_config_write(segment, tokens, run_dir)
        if reason:
            return reason
        if not tokens:
            continue
        name = os.path.basename(tokens[0])
        if name in ("cd", "pushd"):
            target = next((t for t in tokens[1:] if not t.startswith("-")), HOME)
            run_dir = resolve(target, run_dir) if target != "-" else run_dir
            continue
        if written:
            runs = name in SHELLS or name in ("source", ".") or tokens[0] in written or (name in written and "/" in tokens[0])
            for t in tokens if runs else (tokens[1:] if name in INTERPRETERS or name.startswith("python") else []):
                body = written.get(os.path.basename(t), False)
                if body is None:
                    return "the command downloads %s and runs it. Download, read it, then decide." % t
                if body is not False and runs:
                    return "the command writes %s and runs it as a shell script: write it in one step, run it in another." % t
                if body:
                    reason = check_code(body, name, cwd, config, depth)
                    if reason:
                        return reason
        if name == "git":
            reason = check_git_config(tokens)
            if reason:
                return reason
            sub, args = git_subcommand(tokens)
            where = tokens[tokens.index("-C") + 1] if "-C" in tokens[:-1] and tokens.index("-C") < len(tokens) - len(args) else None
            if sub == "push":
                reason = check_push(args, resolve(where, run_dir) if where else run_dir, config)
                if reason:
                    return reason
            elif sub == "add" and any(a in ("-A", "--all", ".", "*", ":/", "-a") for a in args):
                return "git add of everything. Add files by path, so secrets and stray files stay out."
        if name == "gh":
            reason = check_gh(tokens)
            if reason:
                return reason
        code_flags = ("-e", "--eval", "-p", "--print") if name == "node" else ("-c",) if name in INTERPRETERS or name.startswith("python") else ()
        for flag in code_flags:
            if flag in tokens[:-1]:
                reason = check_code(tokens[tokens.index(flag) + 1], name, cwd, config, depth)
                if reason:
                    return reason
        if name in SHELLS and "-c" in tokens[:-1] and depth < 3:
            reason = check_bash(tokens[tokens.index("-c") + 1], cwd, config, depth + 1)
            if reason:
                return reason
        if name == "eval" and depth < 3:
            reason = check_bash(" ".join(tokens[1:]), cwd, config, depth + 1)
            if reason:
                return reason
        reason = check_upload(tokens, run_dir, config)
        if reason:
            return reason
    return None


# --- the other tools --------------------------------------------------------------------------

def secrets_file(name):
    base = os.path.basename((name or "").rstrip("/"))
    return base == ".env" or (base.startswith(".env.") and base != ".env.example")


def check_tool(tool_name, tool_input, cwd):
    if tool_name == "Read" and secrets_file(tool_input.get("file_path")):
        return ENV_MESSAGE
    if tool_name == "Grep":
        glob = tool_input.get("glob", "") or ""
        if secrets_file(tool_input.get("path")) or any(fnmatch.fnmatch(".env", g.split("/")[-1]) for g in re.split(r"[{},]", glob) if g.startswith(".e") or "/.e" in g):
            return ENV_MESSAGE
    if tool_name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        full = os.path.realpath(os.path.join(cwd, os.path.expanduser(path))) if path else ""
        if path and secrets_file(full):
            return "editing %s. Secrets live only in .env, GitHub secrets or Vercel; no session writes them." % os.path.basename(full)
        if path and net_config_path(full):
            return "editing %s, which sets where curl, git or gh connect or holds their credentials." % path
    return None


def main():
    """Fail closed: a crash or an unreadable call refuses (a hook that dies lets the tool run)."""
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise TypeError("the tool call is not an object")
        tool_name, tool_input = data.get("tool_name", ""), data.get("tool_input") or {}
        cwd = data.get("cwd") or os.getcwd()
        config = load_config(cwd)
        reason = check_tool(tool_name, tool_input, cwd)
        if not reason and tool_name == "Bash":
            reason = check_bash(tool_input.get("command", ""), cwd, config)
    except Exception as e:  # noqa: B902
        reason = "the guard failed on this call (%s: %s). Simplify the call." % (type(e).__name__, str(e)[:200])
        data = data if isinstance(locals().get("data"), dict) else {}
    if reason:
        log_refusal(reason, data if isinstance(data, dict) else {})
        print("Refused by docket's guard: " + reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


FAMILIES = (  # the reason's words -> its check id in tools/dk/checks.yaml (`dk why <id>`)
    ("guard.master-push", ("pushes to master go through",)),
    ("guard.crash", ("the guard failed on this call",)),
    ("guard.secret-grep", ("recursive search for a secret",)),
    ("guard.force-push", ("force push", "deleting", "pushing every branch")),
    ("guard.git-add-all", ("git add of everything",)),
    ("guard.download-run", ("download", "and runs it", "writes a file and runs")),
    ("guard.git-config", ("git config", "sets where", "connect or holds", "runs a program")),
    ("guard.upload", ("not origin", "another remote", "sends data", "network socket", "not our own", "is not ours")),
    ("guard.secrets", ("env", "secret", "environment", "token", "credentials")),
)


def log_refusal(reason, data):
    """One row in the block log (~/.docket/dk/blocks.jsonl): the check id and the reason, never the command."""
    check = next((cid for cid, words in FAMILIES if any(w in reason for w in words)), "guard.other")
    row = {"time": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "check": check, "file": "",
           "severity": "blocking", "detail": reason[:300], "resolved": "refused", "branch": "",
           "session": str(data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID", ""))}
    try:
        path = os.environ.get("DK_BLOCKLOG") or os.path.join(os.path.expanduser("~"), ".docket", "dk", "blocks.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    except Exception:  # noqa: B902 - the log never changes the decision
        pass


if __name__ == "__main__":
    main()
