import tkinter as tk

class SvgImage(tk.PhotoImage):
    """Widget which can display images in PGM, PPM, GIF, PNG format."""
    _tksvg_loaded = False
    _svg_options = ['scale', 'scaletowidth', 'scaletoheight']

    def __init__(self, name=None, cnf={}, master=None, **kw):
        # load tksvg
        if not SvgImage._tksvg_loaded:
            if master is None:
                master = tk._default_root
                if not master:
                    raise RuntimeError('Too early to create image')
            master.tk.eval('package require tksvg')
            SvgImage._tksvg_loaded = True
        # remove specific svg options from keywords
        svgkw = {opt: kw.pop(opt, None) for opt in self._svg_options}
        tk.PhotoImage.__init__(self, name, cnf, master, **kw)
        # pass svg options
        self.configure(**svgkw)

    def configure(self, **kw):
        svgkw = {opt: kw.pop(opt) for opt in self._svg_options if opt in kw}
        # non svg options
        if kw:
            tk.PhotoImage.configure(self, **kw)
        # svg options
        options = ()
        for k, v in svgkw.items():
            if v is not None:
                options = options + ('-'+k, str(v))
        self.tk.eval('%s configure -format {svg %s}' % (self.name, ' '.join(options)))