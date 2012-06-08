"""
`%hierarchy` and `%%dot` magics for IPython
===========================================

This extension provides two magics.

First magic is ``%hierarchy``.  This magic command draws hierarchy of
given class or the class of given instance.  For example, the
following shows class hierarchy of currently running IPython shell.::

    %hierarchy get_ipython()


Second magic is ``%%dot``.  You can write graphiz dot language in a
cell using this magic.  Example::

    %%dot -- -Kfdp
    digraph G {
        a->b; b->c; c->d; d->b; d->a;
    }


License for ipython-hierarchymagic
----------------------------------

ipython-hierarchymagic is licensed under the term of the Simplified
BSD License (BSD 2-clause license), as follows:

Copyright (c) 2012 Takafumi Arakaki
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


License for Sphinx
------------------

`run_dot` function in this extension heavily based on Sphinx code
`sphinx.ext.graphviz.render_dot`.  Copyright notice for Sphinx can
be found below.

Copyright (c) 2007-2011 by the Sphinx team (see AUTHORS file).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.core.display import display_png, display_svg

from sphinx.ext.inheritance_diagram import InheritanceGraph


def run_dot(code, options=[], format='png'):
    # mostly copied from sphinx.ext.graphviz.render_dot
    from subprocess import Popen, PIPE
    from sphinx.util.osutil import EPIPE, EINVAL

    dot_args = ['dot'] + options + ['-T', format]
    p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    wentwrong = False
    try:
        # Graphviz may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except (OSError, IOError), err:
        if err.errno != EPIPE:
            raise
        wentwrong = True
    except IOError, err:
        if err.errno != EINVAL:
            raise
        wentwrong = True
    if wentwrong:
        # in this case, read the standard output and standard error streams
        # directly, to get the error message(s)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.wait()
    if p.returncode != 0:
        raise RuntimeError('dot exited with error:\n[stderr]\n{0}'
                           .format(stderr))
    return stdout


@magics_class
class GraphvizMagic(Magics):

    @magic_arguments()
    @argument(
        '-f', '--format', default='png', choices=('png', 'svg'),
        help='output format (png/svg)'
    )
    @argument(
        'options', default=[], nargs='*',
        help='options passed to the `dot` command'
    )
    @cell_magic
    def dot(self, line, cell):
        """Draw a figure using Graphviz dot command."""
        args = parse_argstring(self.dot, line)

        image = run_dot(cell, args.options, format=args.format)

        if args.format == 'png':
            display_png(image, raw=True)
        elif args.format == 'svg':
            display_svg(image, raw=True)


@magics_class
class HierarchyMagic(Magics):

    @magic_arguments()
    @argument(
        '-r', '--rankdir', default='TB',
        help='direction of the hierarchy graph (default: %(default)s)'
    )
    @argument(
        '-s', '--size', default='5.0, 12.0',
        help='size of the generated figure (default: %(default)s)',
    )
    @argument(
        'object',
        help='Class hierarchy of this class or object will be drawn',
    )
    @line_magic
    def hierarchy(self, parameter_s=''):
        """Draw hierarchy of a given class."""
        args = parse_argstring(self.hierarchy, parameter_s)
        obj = self.shell.ev(args.object)
        if isinstance(obj, type):
            objclass = obj
        elif hasattr(obj, "__class__"):
            objclass = obj.__class__
        else:
            raise ValueError(
                "Given object {0} is not a class or an instance".format(obj))
        classpath = self.shell.display_formatter.format(
            objclass, ['text/plain'])['text/plain']
        (dirpath, basepath) = classpath.rsplit('.', 1)
        ig = InheritanceGraph([basepath], dirpath)
        code = ig.generate_dot('inheritance_graph',
                               graph_attrs={'rankdir': args.rankdir,
                                            'size': '"{0}"'.format(args.size)})
        stdout = run_dot(code, format='png')
        display_png(stdout, raw=True)


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(HierarchyMagic)
        ip.register_magics(GraphvizMagic)
        _loaded = True

_loaded = False
