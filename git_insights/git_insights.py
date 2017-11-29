#! usr/bin/python
#coding=utf-8

import subprocess
import os
import sys
import time
import shutil
import codecs
import cgi
import webbrowser
import argparse

from jinja2 import Environment, FileSystemLoader

env = Environment(loader = FileSystemLoader('tpl'))

class GitRepoCollector(object):
    """docstring for GitInfo"""
    def __init__(self, repo_path, repo_branch, output_path):
        super(GitRepoCollector, self).__init__()

        self.git_cmds = {'weekdiff': 'git log -p --since=5.week',
            'gitversion': 'git --version',
            'gitremote': 'git remote -v',
            'total_commits_win': 'git log --oneline --pretty="%h %an" | find /c " " ',
            'total_authors': 'git log --oneline --pretty="%an"'
        }

        self.repo_path = os.path.abspath(repo_path)
        self.repo_branch = repo_branch
        self.output_path = os.path.abspath(output_path)
        self.gen_date = time.asctime(time.localtime(time.time()))
        self.git_commits = []

    def get_pipeout(self, cmd, cwd=None):
        if cwd is None:
            cwd = self.repo_path
        p = subprocess.Popen(cmd, 0, None, None, subprocess.PIPE, subprocess.PIPE, cwd=cwd, shell=True)
        str =''
        for line in p.stdout:
            str = str + line
        p.wait()
        return str.strip('\n')

    def get_weeeks_commits(self, weeks='1'):
        cmd = 'git log --pretty=oneline --format="%h - %ar - %an : %s" --since='+str(weeks)+'.week'
        git_commits = []
        commits_list = self.get_pipeout(cmd).split('\n')
        i = 0
        if commits_list == ['']:
            return ''
        for k in commits_list:
            commit_list = k.split(' - ')
            git_commits.append([])
            git_commits[i].append(commit_list[0])
            git_commits[i].append(commit_list[1])
            s_split = ''.join(commit_list[2:]).split(' : ')
            git_commits[i].append(s_split[0])
            git_commits[i].append(s_split[1])
            i = i + 1
        return git_commits

    def get_git_version(self):
        return self.get_pipeout(self.git_cmds['gitversion'])

    def get_git_remote(self):
        return self.get_pipeout(self.git_cmds['gitremote']).split('\n')[0].split('\t')[1].split(' ')[0]

    def get_git_allcommits(self):
        return self.get_pipeout(self.git_cmds['total_commits_win'])

    def get_git_authors(self):
        return len(set(self.get_pipeout(self.git_cmds['total_authors']).split('\n')))

    def get_diff_stat(self, commit_1, commit_2):
        cmd = ' '.join(['git diff',commit_1,commit_2,'--stat'])
        return self.get_pipeout(cmd)

    def get_commits_stat(self):
        commits_stat={}
        for i in self.git_commits:
            commits_stat[i[0]] = self.get_pipeout(' '.join(['git show ', i[0], '--stat'])).split('\n\n')[2].split('\n')[0:-1]
        return commits_stat

    def generate(self, weeks):
        self.git_commits = self.get_weeeks_commits(weeks)
        self.git_version = self.get_git_version()
        self.git_remote = self.get_git_remote()
        self.total_commits = self.get_git_allcommits()
        self.total_authors = self.get_git_authors()
        print self.git_commits
        if self.git_commits=='':
            self.weekly_diff ='No commit in recent weeks.'
        else:
            self.weekly_diff = self.get_diff_stat(self.git_commits[0][0], self.git_commits[len(self.git_commits)-1][0])
        self.commits_stat = self.get_commits_stat()

def get_gitdiff_patch(): 
    patch = ''
    r_str = get_pipeout(gitcmds['weekdiff'])
    i = 0
    with codecs.open('..git.temp','r', 'utf-8') as fd:
        for line in fd:
            patch = patch + line
            if line.encode('utf-8').startswith('commit '):
                i = i + 1
        # print 'commit number:', i
    os.remove('..git.temp')
    return cgi.escape(patch)

def parse_args():
    parser = argparse.ArgumentParser(description='Git Weekly Report manual')
    parser.add_argument('--d', type=str, default = './', help = 'destination of git repo path')
    parser.add_argument('--branch', type=str, default=None, help = 'git repo branch')
    parser.add_argument('--out', type=str, default='./output/', help = 'output direction')
    args = parser.parse_args()
    return vars(args)    

class ReportGenerator(object):
    """docstring for ReportGenerator"""
    def __init__(self, repo, output_path):
        super(ReportGenerator, self).__init__()
        self.output_path = os.path.abspath(output_path)
        self.repo = repo
        self.init_output()
        
    def init_output(self):
        if os.path.exists(self.output_path):
            os.rename(self.output_path, 'output_del')
            shutil.rmtree('output_del')
        os.mkdir(self.output_path)
        shutil.copytree('./tpl/css', '//'.join([self.output_path,'css']))
        shutil.copytree('./tpl/js', '//'.join([self.output_path,'js']))
        shutil.copytree('./tpl/img', '//'.join([self.output_path,'img']))

    def gen_general_report(self, tpl_name):
        template = env.get_template(tpl_name+'.tpl')
        r_content = template.render(general_info = self.repo)
        with codecs.open('//'.join([self.output_path, tpl_name+'.html']), 'w', 'utf-8') as fd:
            fd.write(r_content)        

    def gen_summary_report(self, tpl_name):
        commits_stat = {}
        for i, v in self.repo.commits_stat.items():
            k = 0; str_f = ''
            for j in v:
                str_f = str_f + "'<a href='./detail.html#" + str(i) + str(k) + "'>" + j + "</a><br>"
                k = k + 1
            commits_stat[i] = str_f
            print commits_stat[i]
            # commits_stat[i] = cgi.escape('<a>'+ '</a><br><a>'.join(v) + '</a>')
        template = env.get_template(tpl_name+'.tpl')
        r_content = template.render(git_list = self.repo.git_commits, git_weekly_diff=self.repo.weekly_diff,commits_stat = commits_stat)
        with codecs.open('//'.join([self.output_path, tpl_name+'.html']), 'w', 'utf-8') as fd:
            fd.write(r_content)

    def gen_detail_report(self, tpl_name):
        new_patch = ''
        if self.repo.git_commits=='':
            new_patch = 'No commit in recent weeks.'
        else:
            patch = self.repo.get_pipeout(self.repo.git_cmds['weekdiff'])
            patch = cgi.escape(patch).decode('utf-8')
            i = -1; j = 0
            for line in patch.split('\n'):
                if line.startswith('commit '):
                    i = i + 1
                    j = 0
                if line.startswith('diff --git'):
                    mao = str(self.repo.git_commits[i][0]) + str(j)
                    line = "<code name='" + mao + "' id='" + mao +"'></code>" + line + "------------------" + mao + "\n"
                    j = j + 1
                if line.startswith('+'):
                    line = '<code style="color: red">' + line + "</code>"
                if line.startswith('-'):
                    line = '<code style="color: green">' + line + "</code>"
                new_patch = new_patch + line + "\n"

        # patch = '<code style="color: red">' + patch + "</code>"
        template = env.get_template(tpl_name+'.tpl')
        r_content = template.render(git_diff_patch=new_patch)
        
        with codecs.open('//'.join([self.output_path, tpl_name+'.html']), 'w', 'utf-8') as fd:
            fd.write(r_content)   

    def generate_report(self):
        self.gen_general_report('general')
        self.gen_summary_report('summary')
        self.gen_detail_report('detail')

def main():

    args = parse_args()
    # webbrowser.open('//'.join([os.getcwd(),args['out'],'general.html']))

    args['d'] = 'C:\git\mcu_PSDK_test_imx8qxp_m4\mcu-sdk'
    # args['d'] = '../'
    repo = GitRepoCollector(args['d'], 'master', args['out'])
    repo.generate(1)
    report = ReportGenerator(repo, args['out'])
    report.generate_report()

if __name__ == '__main__':
    main()