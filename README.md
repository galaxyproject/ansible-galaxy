Galaxy
======

An [Ansible][ansible] role for installing and managing [Galaxy][galaxyproject] servers.  Despite the name confusion,
[Galaxy][galaxyproject] bears no relation to [Ansible Galaxy][ansiblegalaxy].

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/

Requirements
------------

This role has the same dependencies as the git module. In addition, [Python virtualenv][venv] is required (as is
[pip][pip], but pip will be automatically installed with virtualenv). These can easily be installed via a pre-task in
the same play as this role:

```yaml
- hosts: galaxyservers
  pre_tasks:
    - name: Install Dependencies
      apt:
        name: "{{ item }}"
      become: yes
      when: ansible_os_family == 'Debian'
      with_items:
        - git
        - python-virtualenv
    - name: Install Dependencies
      yum:
        name: "{{ item }}"
      become: yes
      when: ansible_os_family == 'RedHat'
      with_items:
        - mercurial
        - python-virtualenv
  roles:
    - galaxyprojectdotorg.galaxy
```

If your `git` executable is not on `$PATH`, you can specify its location with the `git_executable` variable. Likewise
with the `virtualenv` executable and corresponding `pip_virtualenv_command` variable.

[git]: http://git-scm.com/
[venv]: http://virtualenv.readthedocs.org/
[pip]: http://pip.readthedocs.org/

Role Variables
--------------

### Required variables ###

- `galaxy_server_dir`: Filesystem path where the Galaxy server code will be installed (cloned).

### Optional variables ###

New options for Galaxy 18.01 and later:

- `galaxy_config_style` (default: `ini-paste`): The type of Galaxy configuration file to write, `ini-paste` for the
  traditional PasteDeploy-style INI file, or `yaml` for the YAML format supported by uWSGI.
- `galaxy_app_config_section` (default: depends on `galaxy_config_style`): The config file section under which the
  Galaxy config should be placed (and the key in `galaxy_config` in which the Galaxy config can be found. If
  `galaxy_config_style` is `ini-paste` the default is `app:main`. If `galaxy_config_style` is `yaml`, the default is
  `galaxy`.
- `galaxy_uwsgi_yaml_parser` (default: `internal`): Controls whether the `uwsgi` section of the Galaxy config file will
  be written in uWSGI-style YAML or real YAML. By default, uWSGI's internal YAML parser does not support real YAML. Set
  to `libyaml` to write real YAML, if you are using uWSGI that has been compiled with libyaml. see
  [unbit/uwsgi#863][uwsgi-863] for details.
- To override the default uWSGI configuration, place your uWSGI options under the `uwsgi` key in the `galaxy_config`
  dictionary explained below. Note that the defaults are not merged with your config, so you should fully define the
  `uwsgi` section if you choose to set it. Note that **regardless of which `galaxy_uwsgi_yaml_parser` you use, this
  should be written in real YAML** because Ansible parses it with libyaml, which does not support the uWSGI internal
  parser's duplicate key syntax. This role will automatically convert the proper YAML to uWSGI-style YAML as necessary.

[uwsgi-863]: https://github.com/unbit/uwsgi/issues/863

Several variables control which functions this role will perform (all default to `yes`):

- `galaxy_manage_clone`: Clone Galaxy from the source repository and maintain it at a specified version (commit), as
  well as set up a [virtualenv][virtualenv] from which it can be run.
- `galaxy_manage_static_setup`: Manage "static" Galaxy configuration files - ones which are not modifiable by the Galaxy
  server itself. At a minimum, this is the primary Galaxy configuration file, `galaxy.ini`.
- `galaxy_manage_mutable_setup`: Manage "mutable" Galaxy configuration files - ones which are modifiable by Galaxy (e.g.
  as you install tools from the Galaxy Tool Shed).
- `galaxy_manage_database`: Upgrade the database schema as necessary, when new schema versions become available.
- `galaxy_fetch_dependencies`: Fetch Galaxy dependent modules to the Galaxy virtualenv.
- `galaxy_manage_errordocs`: Install Galaxy-styled 413 and 502 HTTP error documents for nginx

You can control various things about where you get Galaxy from, what version you use, and where its configuration files
will be placed:

- `galaxy_config`: The contents of the Galaxy configuration file (`galaxy.ini` by default) are controlled by this
  variable. It is a hash of hashes (or dictionaries) that will be translated in to the configuration
  file. See the Example Playbooks below for usage.
- `galaxy_config_files`: List of hashes (with `src` and `dest` keys) of files to copy from the control machine.
- `galaxy_repo` (default: `https://github.com/galaxyproject/galaxy.git`): Upstream Git repository from which Galaxy
  should be cloned.
- `galaxy_commit_id` (default: `master`): A commit id, tag, branch, or other valid Git reference that Galaxy should be
  updated to. Specifying a branch will update to the latest commit on that branch. A debugging message will notify you
  if the current commit of your Galaxy server is different from this value. There is no harm in this, but:
    - if this annoys you, you must use a full (long) commit id to prevent that task from reporting **changed** on every
      run, and
    - using a real commit id is the only way to explicitly lock Galaxy at a specific version.
- `galaxy_force_checkout` (default: `no`): If `yes`, any modified files in the Galaxy repository will be discarded.
- `galaxy_requirements_file` (default: `<galaxy_server_dir>/lib/galaxy/dependencies/pinned-requirements.txt`): The
  Python `requirements.txt` file that should be used to install Galaxy dependent modules using pip.
- `galaxy_venv_dir` (default: `<galaxy_server_dir>/.venv`): The role will create a [virtualenv][virtualenv] from which
  Galaxy will run, this controls where the virtualenv will be placed.
- `galaxy_config_dir` (default: `<galaxy_server_dir>`): Directory that will be used for "static" configuration files.
- `galaxy_mutable_config_dir` (default: `<galaxy_server_dir>`): Directory that will be used for "mutable" configuration
  files, must be writable by the user running Galaxy.
- `galaxy_mutable_data_dir` (default: `<galaxy_server_dir>/database`): Directory that will be used for "mutable" data
  and caches, must be writable by the user running Galaxy.
- `galaxy_config_file` (default: `<galaxy_config_dir>/galaxy.ini`): Galaxy's primary configuration file.
- `galaxy_shed_tool_conf_file` (default: `<galaxy_mutable_config_dir>/shed_tool_conf.xml`): Configuration file for tools
  installed from the Galaxy Tool Shed.
- `galaxy_config_templates`: List of hashes (with `src` and `dest` keys) of templates to fill from the control machine.
- `galaxy_admin_email_to`: If set, email this address when Galaxy has been updated. Assumes mail is properly configured
  on the managed host.
- `galaxy_admin_email_from`: Address to send the aforementioned email from.
- `galaxy_errordocs_dir`: Install Galaxy-styled HTTP 413 and 502 error documents under this directory. The 502 message
  uses nginx server side includes to allow administrators to create a custom message in `~/maint` when Galaxy is down.
  nginx must be configured separately to serve these error documents.
- `galaxy_errordocs_server_name` (default: Galaxy): used to display the message "`galaxy_errdocs_server_name` cannot be
  reached" on the 502 page.
- `galaxy_errordocs_prefix` (default: `/error`): Web-side path to the error document root.


Dependencies
------------

None

Example Playbook
----------------

**Basic:**

Install Galaxy on your local system with all the default options:

```yaml
- hosts: localhost
  vars:
    galaxy_server_dir: /srv/galaxy
  connection: local
  roles:
     - galaxy
```

Once installed, you can start with:

```console
$ cd /srv/galaxy
$ sh run.sh
```

**Advanced:**

Install Galaxy with the clone and configs owned by a different user than the user running Galaxy, and backed by
PostgreSQL, on the hosts in the `galaxyservers` group in your inventory. Additionally, use the 18.01+ style YAML config
and start two [job handler mules][deployment-options].

[deployment-options]: https://docs.galaxyproject.org/en/master/admin/scaling.html#deployment-options

```yaml
- hosts: galaxyservers
  vars:
    galaxy_config_style: yaml
    galaxy_server_dir: /opt/galaxy/server
    galaxy_config_dir: /opt/galaxy/config
    galaxy_mutable_config_dir: /var/opt/galaxy/config
    galaxy_mutable_data_dir: /var/opt/galaxy/data
    galaxy_commit_id: release_18.05
    postgresql_objects_users:
      - name: galaxy
        password: null
    postgresql_objects_databases:
      - name: galaxy
        owner: galaxy
    galaxy_config:
      uwsgi:
        socket: 127.0.0.1:4001
        buffer-size: 16384
        processes: 1
        threads: 4
        offload-threads: 2
        static-map:
          - /static/style={{ galaxy_server_dir }}/static/style/blue
          - /static={{ galaxy_server_dir }}/static
        master: true
        virtualenv: "{{ galaxy_venv_dir }}"
        pythonpath: "{{ galaxy_server_dir }}/lib"
        module: galaxy.webapps.galaxy.buildapp:uwsgi_app()
        thunder-lock: true
        die-on-term: true
        hook-master-start:
          - unix_signal:2 gracefully_kill_them_all
          - unix_signal:15 gracefully_kill_them_all
        py-call-osafterfork: true
        enable-threads: true
        mule: lib/galaxy/main.py
        mule: lib/galaxy/main.py
        farm: job-handlers:1,2
      galaxy:
        database_connection: "postgresql:///galaxy?host=/var/run/postgresql"
  pre_tasks:
    - name: Create Galaxy code owner user
      user:
        name: gxcode
        comment: "Galaxy Code"
        system: yes
        home: /opt/galaxy
        createhome: yes
      become: yes
    - name: Create Galaxy runtime user
      user:
        name: galaxy
        comment: "Galaxy Server"
        system: yes
        home: /var/opt/galaxy
        createhome: yes
      become: yes
    - name: Install Dependencies
      apt:
        name: "{{ item }}"
      become: yes
      with_items:
        - git
        - python-psycopg2
        - python-virtualenv
    # Precreating the mutable config directory may be necessary (it's not in our example since we set the user's home
    # directory to galaxy_mutable_config_dir's parent).
    #- name: Create mutable configuration file directory
    #  file:
    #    path: "{{ galaxy_mutable_config_dir }}"
    #    owner: galaxy
    #    state: directory
    #  become: yes
  roles:
    # Install with:
    #   % ansible-galaxy install galaxyproject.postgresql
    - galaxyproject.postgresql
    # Install with:
    #   % ansible-galaxy install natefoo.postgresql_objects
    - role: natefoo.postgresql_objects
      become: yes
      become_user: postgres
    - role: galaxy
      become: yes
      become_user: gxcode
      galaxy_manage_mutable_setup: no
      galaxy_manage_database: no
    - role: galaxy
      become: yes
      become_user: galaxy
      galaxy_manage_clone: no
      galaxy_manage_static_setup: no
```

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

This role was written and contributed to by the following people:

[Enis Afgan](https://github.com/afgane)  
[Dannon Baker](https://github.com/dannon)  
[Simon Belluzzo](https://github.com/simonalpha)  
[John Chilton](https://github.com/jmchilton)  
[Nate Coraor](https://github.com/natefoo)  
