import contextlib
import datetime
import os
import subprocess
import sys
from argparse import ArgumentParser
from datetime import datetime
from importlib import resources

import fileunity


class Prog:
    def get_name(self, key, /):
        func = self.__getattribute__("name_" + key)
        ans = func()
        if type(ans) in [tuple, list]:
            ans = os.path.join(*ans)
        return ans
    def calc(self, key, /):
        func = self.__getattribute__("calc_" + key)
        return func()
    def make_dir(self):
        root = os.path.expanduser(self.root)
        project_dir = os.path.join(root, self.project)
        self.project_dir = os.path.abspath(project_dir)
        if os.path.exists(self.project_dir):
            raise FileExistsError
        if self.github_user is None:
            os.mkdir(self.project_dir)
            return
        args = [
            'git',
            'init',
            self.project_dir,
        ]
        subprocess.run(args=args, check=True)
    def git_commit(self, message, *, allow_empty=False):
        if self.github_user is None:
            return
        with contextlib.chdir(self.project_dir):
            args="git stage .".split()
            subprocess.run(args=args, check=True)
            args=[
                'git',
                'commit',
                '--message',
                message,
            ]
            if allow_empty:
                args.append("--allow-empty")
            if self.git_author is not None:
                args.append('--author')
                args.append(self.git_author)
            subprocess.run(args=args, check=True)
    def __getattr__(self, key):
        if type(key) is not str:
            raise TypeError
        if key.startswith('__'):
            raise KeyError
        if not key.startswith('_'):
            return getattr(self, "_" + key)
        key = key[1:]
        if key.endswith("_textfile"):
            text = getattr(self, key[:-9] + "_text")
            if text is None:
                ans = None
            else:
                ans = self.get_name(key)
                fileunity.TextUnit.by_str(text).save(ans)
        elif key.endswith("_dir"):
            ans = self.get_name(key)
            os.mkdir(ans)
        else:
            ans = self.calc(key)
        setattr(self, '_' + key, ans)
        return ans
    def __init__(self, args):
        ns = self.parser.parse_args(args=args)
        kwargs = vars(ns)
        for k, v in kwargs.items():
            setattr(self, k, v)
    def run(self):
        self.make_dir()
        with contextlib.chdir(self.project_dir):
            self.git_commit("Initial Commit", allow_empty=True)
            self.pyproject_textfile
            self.setup_textfile
            self.gitignore_textfile
            self.manifest_textfile
            self.init_textfile
            self.main_textfile
            self.git_commit("Version 0.0.0")
    def name_src_dir(self):
        return "src"
    def name_pkg_dir(self):
        return self.src_dir, self.project
    def name_init_textfile(self):
        return self.pkg_dir, '__init__.py'
    def name_main_textfile(self):
        return self.pkg_dir, '__main__.py'
    def name_pyproject_textfile(self):
        return "pyproject.toml"
    def name_license_textfile(self):
        return "LICENSE.txt"
    def name_readme_textfile(self):
        return "README.rst"
    def name_manifest_textfile(self):
        return "MANIFEST.in"
    def name_setup_textfile(self):
        return "setup.cfg"
    def name_gitignore_textfile(self):
        return ".gitignore"
    def calc_init_text(self):
        ans = resources.read_text("hieronymus.drafts", "init.txt")
        return ans
    def calc_main_text(self):
        ans = resources.read_text("hieronymus.drafts", "main.txt")
        ans = ans.format(project=self.project)
        return ans
    def calc_manifest_text(self):
        return ""
    def calc_license_text(self):
        if self.author is None:
            return None
        ans = resources.read_text("hieronymus.drafts", "license.txt")
        ans = ans.format(year=self.year, author=self.author)
        return ans
    def calc_gitignore_text(self):
        if self.github_user is None:
            return None
        ans = resources.read_text("hieronymus.drafts", "gitignore.txt")
        return ans
    def calc_config_data(self):
        try:
            text = resources.read_text("hieronymus", "config.toml")
        except:
            text = ""
        ans = fileunity.TOMLUnit.data_by_str(text)
        return ans
    def calc_config_author(self):
        ans = self.config_data.get('author')
        if (ans is None) or (type(ans) is str):
            return ans
        raise TypeError
    def calc_config_email(self):
        ans = self.config_data.get('email')
        if (ans is None) or (type(ans) is str):
            return ans
        raise TypeError
    def calc_config_github_user(self):
        ans = self.config_data.get('github_user')
        if (ans is None) or (type(ans) is str):
            return ans
        raise TypeError
    def calc_config_root(self):
        ans = self.config_data.get('root', '.')
        if (ans is None) or (type(ans) is str):
            return ans
        raise TypeError
    def calc_git_author(self):
        if self.final_author is None:
            return None
        ans = self.final_author
        if self.email is not None:
            ans = f"{ans} <{self.email}>"
        return ans
    def calc_final_author(self):
        if self.author is None:
            return self.email
        else:
            return self.author
    def calc_parser(self):
        ans = ArgumentParser(fromfile_prefix_chars="@")
        ans.add_argument('project', nargs='?', default='a', type=self.nameType)
        ans.add_argument('--description')
        ans.add_argument('--author', default=self.config_author, type=self.stripType)
        ans.add_argument('--email', default=self.config_email, type=self.stripType)
        ans.add_argument('--root', default=self.config_root)
        ans.add_argument('--year', default=datetime.now().year)
        ans.add_argument('--requires-python', default=self.default_requires_python())
        ans.add_argument('--github-user', default=self.config_github_user)
        return ans
    def calc_readme_text(self):
        blocknames = "heading overview installation license links credits".split()
        blocks = [getattr(self, x + "_rst_block") for x in blocknames]
        blocks = [x for x in blocks if x is not None]
        blocks = ['\n'.join(x) for x in blocks if type(x) is not str]
        ans = "\n\n".join(blocks)
        return ans
    def calc_heading_rst_block(self):
        lining = "=" * len(self.project)
        ans = [lining, self.project, lining]
        return ans
    def calc_overview_rst_block(self):
        if self.description is None:
            return None
        heading = "Overview"
        lining = "-" * len(heading)
        ans = [heading, lining, "", self.description]
        return ans
    def calc_installation_rst_block(self):
        heading = "Installation"
        lining = "-" * len(heading)
        sentence = f"To install {self.project}, you can use `pip`. Open your terminal and run:"
        codestart = ".. code-block:: bash"
        codeline = f"    pip install {self.project}"
        ans = [heading, lining, "", sentence, "", codestart, "", codeline]
        return ans
    def calc_license_rst_block(self):
        if self.license_textfile is None:
            return None
        heading = "License"
        lining = "-" * len(heading)
        sentence = "This project is licensed under the MIT License."
        ans = [heading, lining, "", sentence]
        return ans
    def calc_links_rst_block(self):
        if len(self.urls) == 0:
            return None
        heading = "Links"
        lining = "-" * len(heading)
        points = list()
        for k, v in self.urls.items():
            point = f"* `{k} <{v}>`_"
            points.append(point)
        ans = [heading, lining, ""] + points
        return ans
    def calc_credits_rst_block(self):
        if self.final_author is None:
            return None
        heading = "Credits"
        lines = list()
        lines.append(heading)
        lines.append("-" * len(heading))
        if self.author is not None:
            lines.append("- Author: " + self.author)
        if self.email is not None:
            lines.append("- Email: " + self.email)
        lines.append("")
        lines.append(f"Thank you for using {self.project}!")
        return lines
    def calc_setup_text(self):
        return "\n"
    def calc_pyproject_text(self):
        return fileunity.TOMLUnit.str_by_data(self.pyproject_data)
    def calc_pyproject_data(self):
        ans = dict()
        ans['build-system'] = self.build_system_data
        ans['project'] = self.project_data
        return ans
    def calc_build_system_data(self):
        return {
            "requires" : ["setuptools>=61.0.0"],
            "build-backend" : "setuptools.build_meta",
        }
    def calc_final_description(self):
        if self.description is None:
            return self.project
        else:
            return self.description
    def calc_project_data(self):
        ans = dict()
        ans['name'] = self.project
        ans['version'] = "0.0.0"
        ans['description'] = self.final_description
        if self.license_textfile is not None:
            ans['license'] = {'file' : self.license_textfile}
        ans['readme'] = self.readme_textfile
        if self.authors is not None:
            ans['authors'] = self.authors
        ans['classifiers'] = self.classifiers
        ans['keywords'] = []
        ans['dependencies'] = []
        ans['requires-python'] = self.requires_python
        ans['urls'] = self.urls
        return ans
    def calc_urls(self):
        ans = dict()
        ans['Download'] = f"https://pypi.org/project/{self.project.replace('_', '-')}/#files"
        if self.github_user is not None:
            ans['Source'] = f"https://github.com/{self.github_user}/{self.project}"
        return ans
    def calc_classifiers(self):
        ans = list()
        if self.license_textfile is not None:
            ans.append("License :: OSI Approved :: MIT License")
        ans.append("Programming Language :: Python")
        ans.append("Programming Language :: Python :: 3")
        return ans
    def calc_authors(self):
        if self.final_author is None:
            return None
        if self.email is None:
            return [dict(name=self.final_author)]
        else:
            return [dict(name=self.final_author, email=self.email)]
    @staticmethod
    def default_requires_python():
        assert sys.version_info[0] == 3
        return f">=3.{sys.version_info[1]}"
    @staticmethod
    def nameType(value, /):
        value = Prog.stripType(value)
        normpath = os.path.normpath(value)
        assert value == normpath
        x, y = os.path.split(value)
        assert x == ""
        return value
    @staticmethod
    def stripType(value, /):
        value = str(value)
        value = value.strip()
        return value

