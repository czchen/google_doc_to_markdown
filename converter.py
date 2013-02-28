#!/usr/bin/env python3
import argparse
import re
import sys

from html import parser

class HTMLParser(parser.HTMLParser):
    _OLLI_INDENT = 3
    _CODE_INDENT = 4

    _DEFAULT_STATE = {
            "name": "start",
            "indent": 0,
    }

    def __init__(self, output, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = [self._DEFAULT_STATE]
        self._output = output

    def _get_pop_state_endtag(tag, **kwargs):
        def _func(self, tag_):
            if tag == tag_:
                self._state.pop(-1)
                if "enter" in kwargs:
                    self._output.write("\n" * kwargs["enter"])
                if "indent" in kwargs:
                    self._indent -= kwargs["indent"]
        return _func

    def _null_func(self, *args, **kwargs):
        pass

    def _get_current_state(self):
        return self._state[-1]

    def _get_current_state_name(self):
        return self._get_current_state()["name"]

    def _get_current_indent(self):
        return self._get_current_state()["indent"]

    def _escape(self, data):
        return re.sub(r"([_])", r"\\\1", data)

    def _write_data(self, data):
        self._output.write(self._escape(data))

    def handle_starttag(self, tag, attrs):
        getattr(self, "_{}_handle_starttag".format(self._get_current_state_name()), HTMLParser._null_func)(tag, attrs)

    def handle_endtag(self, tag):
        getattr(self, "_{}_handle_endtag".format(self._get_current_state_name()), HTMLParser._null_func)(tag)

    def handle_data(self, data):
        getattr(self, "_{}_handle_data".format(self._get_current_state_name()), HTMLParser._null_func)(data)

    # start
    def _start_handle_starttag(self, tag, attrs):
        if tag == "body":
            self._state.append({
                "name": "body",
                "indent": 0,
            })

    def _generic_handle_starttag(self, tag, attrs):
        if tag == "ol":
            for key, value in attrs:
                if key == "class":
                    if value == "c0":
                        self._get_current_state()["indent"] = 0
                    if value == "c15":
                        self._get_current_state()["indent"] = self._OLLI_INDENT
            self._state.append({
                "name": "ol",
                "indent": self._get_current_indent(),
            })
            return

        match = re.match("h(\d+)", tag)
        if match:
            level = int(match.group(1))
            self._output.write("#" * level + " ")
            self._state.append({
                "name": "h",
                "indent": self._get_current_indent()
            })
            return

        if tag == "a":
            self._state.append({
                "name": "a",
                "indent": self._get_current_indent(),
                "attrs": attrs,
            })
            return

    # body
    _body_handle_starttag = _generic_handle_starttag

    _body_handle_endtag = _get_pop_state_endtag("body")

    # h
    _h_handle_data = _write_data

    def _h_handle_endtag(self, tag):
        match = re.match("h(\d+)", tag)
        if match:
            self._output.write("\n")
            self._state.pop(-1)

    # ol
    def _ol_handle_starttag(self, tag, attrs):
        if tag == "li":
            self._output.write(" " * self._get_current_indent() + "* ")
            self._state.append({
                "name": "olli",
                "indent": self._get_current_indent(),
            })
            return

    _ol_handle_endtag = _get_pop_state_endtag("ol", enter=1)

    # olli
    _olli_handle_starttag = _generic_handle_starttag

    _olli_handle_data = _write_data

    _olli_handle_endtag = _get_pop_state_endtag("li", enter=1)

    # a
    def _a_handle_data(self, data):
        href = ""
        for key, value in self._get_current_state()["attrs"]:
            if key == "href":
                href = value
                break
        self._output.write("[{}]({})".format(self._escape(data), href))

    _a_handle_endtag = _get_pop_state_endtag("a")


def parse_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("src", nargs=1, type=str)
    parser.add_argument("dst", nargs="?", type=str)
    args = parser.parse_args()
    
    config = {}

    config["src"] = args.src[0]

    if args.dst is None:
        index = config["src"].rfind(".")
        if index == -1:
            config["dst"] = "{}.md".format(config["src"])
        else:
            config["dst"] = "{}.md".format(config["src"][:index])
    else:
        config["dst"] = args.dst[0]

    return config

def main():
    config = parse_config()
    with open(config["src"], "r") as src, open(config["dst"], "w") as dst:
        parser = HTMLParser(dst)
        parser.feed(src.read())

if __name__ == "__main__":
    main()
