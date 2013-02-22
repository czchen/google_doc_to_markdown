#!/usr/bin/env python3
import argparse
import re
import sys

from html import parser

class HTMLParser(parser.HTMLParser):
    _INDENT = 3
    _CODE_INDENT = 4

    def __init__(self, output, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output = output
        self._state = ["start"]
        self._indent = 0
        self._attrs = None

    @staticmethod
    def _escape(data):
        return data

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

    def _write_data(self, data):
        self._output.write(self._escape(data))

    def handle_starttag(self, tag, attrs):
        getattr(self, "_{}_handle_starttag".format(self._state[-1]), HTMLParser._null_func)(tag, attrs)

    def handle_endtag(self, tag):
        getattr(self, "_{}_handle_endtag".format(self._state[-1]), HTMLParser._null_func)(tag)

    def handle_data(self, data):
        getattr(self, "_{}_handle_data".format(self._state[-1]), HTMLParser._null_func)(data)

    # start
    def _start_handle_starttag(self, tag, attrs):
        if tag == "body":
            self._state.append("body")

    # body
    def _body_handle_starttag(self, tag, attrs):
        if tag == "ol":
            self._state.append("ol")

        match = re.match("h(\d+)", tag)
        if match:
            level = int(match.group(1))
            self._output.write(" " * self._indent + "#" * level + " ")
            self._state.append("h")
            return

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
            self._output.write(" " * self._indent + "* ")
            self._state.append("olli")
            return

    _ol_handle_endtag = _get_pop_state_endtag("ol", enter=1)

    # olli
    def _olli_handle_starttag(self, tag, attrs):
        if tag == "a":
            self._attrs = attrs
            self._state.append("a")
            return

    _olli_handle_data = _write_data

    _olli_handle_endtag = _get_pop_state_endtag("li", enter=1)

    # a
    def _a_handle_data(self, data):
        href = ""
        for key, value in self._attrs:
            if key == "href":
                href = value
                break
        self._output.write("[{}]({})".format(data, href))

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