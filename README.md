Galaxy
======

An [Ansible][ansible] role for installing and managing [Galaxy][galaxyproject] servers.  Despite the name confusion,
[Galaxy][galaxyproject] bears no relation to [Ansible Galaxy][ansiblegalaxy].

Getting started with this module? Check out our [Tutorial](https://training.galaxyproject.org/training-material/topics/admin/tutorials/ansible-galaxy/tutorial.html)

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/

Requirements
------------

This role has the same dependencies as the git module. In addition, [pip][pip] and [Python virtualenv][venv] are required. These can easily be installed via a pre-task in
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
        - python-pip
        - python-virtualenv
    - name: Install Dependencies
      yum:
        name: "{{ item }}"
      become: yes
      when: ansible_os_family == 'RedHat'
      with_items:
        - git
        - python-virtualenv
  roles:
    - galaxyproject.galaxy
```

If your `git` executable is not on `$PATH`, you can specify its location with the `git_executable` variable. Likewise
with the `virtualenv` executable and corresponding `galaxy_virtualenv_command` variable.

[git]: http://git-scm.com/
[venv]: http://virtualenv.readthedocs.org/
[pip]: http://pip.readthedocs.org/

Role Variables
--------------

Not all variables are listed or explained in detail. For additional information about less commonly used variables, see
the [defaults file][defaults].

[defaults]: defaults/main.yml

Many variables control where specific files are placed and where Galaxy writes data. In order to simplify configuration,
you may select a *layout* with the `galaxy_layout` variable. Which layout you choose affects the required variables.

### Required variables ###

If using any layout other than `root-dir`:

- `galaxy_server_dir`: Filesystem path where the Galaxy server code will be installed (cloned).

If using `root-dir`:

- `galaxy_root`: Filesystem path of the root of a Galaxy deployment, the Galaxy server code will be installed in to a
  subdirectory of this directory.

### Optional variables ###

The `galaxy_config_perms` option controls the permissions that Galaxy configuration files will be set to. This option
has been added in version 0.9.18 of the role and the default value is `0640` (user read-write, group read-only, other
users have no permissions). **In older versions, the role did not control the permissions of configuration files, so be
aware that your configuration file permissions may change as of 0.9.18 and later.**

**Layout control**

- `galaxy_layout`: available layouts can be found in the [vars/][vars] subdirectory and possible values include:
  - `root-dir`: Everything is laid out in subdirectories underneath a single root directory.
  - `opt`: An [FHS][fhs]-conforming layout across multiple directories such as `/opt`, `/etc/opt`, etc.
  - `legacy-improved`: Everything underneath the Galaxy server directory, as with `run.sh`.
  - `legacy`: The default layout prior to the existence of `galaxy_layout` and currently the default so as not to break
    existing usage of this role.
  - `custom`: Reasonable defaults for custom layouts, requires setting a few variables as described in
    [vars/layout-custom.yml][custom]

Either the `root-dir` or `opt` layout is recommended for new Galaxy deployments.

Options below that control individual file or subdirectory placement can still override defaults set by the layout.

[vars]: vars/
[custom]: vars/layout-custom.yml
[fhs]: http://www.pathname.com/fhs/

**Process control with Gravity**

The role can manage the Galaxy service using [gravity][gravity]. This is the default for Galaxy 22.05 and later.
Additionally, support for the `galaxy_restart_handler_name` variable has been removed. If you need to enable your own
custom restart handler, you can use the "`listen`" option to the handler as explained in the [handler
documentation](https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html#using-variables-with-handlers).
The handler should "listen" to the topic `"restart galaxy"`.

[gravity]: https://github.com/galaxyproject/gravity

**Galaxy Themes**

From release 22.01, Galaxy users can select between different UI [themes][themes]. You can define themes using the
`galaxy_themes` variable, the syntax of which is the same as the `themes_conf.yml` file described [in the themes
training][themes].

The `galaxy_manage_themes` variable controls whether the role manages theme configs and is automatically enabled if
`galaxy_themes` is defined. If you just want to load the the sample themes from Galaxy's
[themes_conf.yml.sample][themes_conf_sample] without defining your own, you can manually set `galaxy_manage_themes` to
`true`.

[themes]: https://training.galaxyproject.org/training-material/topics/admin/tutorials/customization/tutorial.html
[themes_conf_sample]: https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy/config/sample/themes_conf.yml.sample

**Galaxy Subdomains**

From release 22.01 Galaxy can serve different static content and themes per host (e.g. subdomain).

By setting `galaxy_manage_subdomain_static: yes` you enable the creation of static directories and configuration per host.

In order to use this feature, you need to create the following directory structure under files/ (customizable with the `galaxy_themes_ansible_file_path` variable):

~~~bash
files/galaxy/static
├──<subdomain-name-1>
│   └── static
│       ├── dist (optional)
│       │   └── some-image.png
│       ├── images (optional)
│       │   └── more-content.jpg
│       └── welcome.html (optional, galaxyproject.org will be displayed otherwise.)
├── <subdomain-name-2>                            
│   └── static
│       ├── dist (optional)
│       │   ├── another-static-image.svg
│       │   └── more-static-content-2.svg
│       └── welcome.html (optional)
... (and many more subdomains)
~~~

Where the <subdomain-name-1> should exactly match your subdomain's name. The subdirectory `static` is mandatory, while all subdirectories in `static` are optional. Which subdirectories and files are copied is managed by the `static_galaxy_themes_keys` variable.

Also make sure that you set `galaxy_themes_welcome_url_prefix`, so your welcome pages are templated correctly.

It is mandatory to set the variables under `galaxy_themes_subdomains` as shown in the example in [defaults/main.yml](defaults/main.yml). If you enabled the `galaxy_manage_host_filters` variable, you can also specify the tool sections that should be shown for each individual subdomain.

Each subdomain can be given its own theme, which is defined under the `theme` key of the subdomain's entry in `galaxy_themes_subdomains`. This theme will be the default for the subdomain, and any other themes defined globally for the server will also be available for the user to select. If a subdomain's `theme` is not defined, the global default is used. An example is provided in [defaults/main.yml](defaults/main.yml).

**Feature control**

Several variables control which functions this role will perform (all default to `yes` except where noted):

- `galaxy_create_user` (default: `no`): Create the Galaxy user. Running as a dedicated user is a best practice, but most
  production Galaxy instances submitting jobs to a cluster will manage users in a directory service (e.g.  LDAP). This
  option is useful for standalone servers. Requires superuser privileges.
- `galaxy_manage_paths` (default: `no`): Create and manage ownership/permissions of configured Galaxy paths. Requires
  superuser privileges.
- `galaxy_manage_clone`: Clone Galaxy from the source repository and maintain it at a specified version (commit), as
  well as set up a [virtualenv][virtualenv] from which it can be run.
- `galaxy_manage_download`: Download and unpack Galaxy from a remote archive url, as
  well as set up a [virtualenv][virtualenv] from which it can be run.
- `galaxy_manage_existing`: Take over a Galaxy directory that already exists, as
  well as set up a [virtualenv][virtualenv] from which it can be run. `galaxy_server_dir` must point to the path which
  already contains the source code of Galaxy.
- `galaxy_manage_static_setup`: Manage "static" Galaxy configuration files - ones which are not modifiable by the Galaxy
  server itself. At a minimum, this is the primary Galaxy configuration file, `galaxy.ini`.
- `galaxy_manage_mutable_setup`: Manage "mutable" Galaxy configuration files - ones which are modifiable by Galaxy (e.g.
  as you install tools from the Galaxy Tool Shed).
- `galaxy_manage_database`: Upgrade the database schema as necessary, when new schema versions become available.
- `galaxy_fetch_dependencies`: Fetch Galaxy dependent modules to the Galaxy virtualenv.
- `galaxy_build_client`: Build the Galaxy client application (web UI).
- `galaxy_client_make_target` (default: `client-production-maps`): Set the client build type. Options include: `client`,
  `client-production` and `client-production-maps`. See [Galaxy client readme][client-build] for details.
- `galaxy_manage_systemd` (default: `no`): Install a [systemd][systemd] service unit to start and stop Galaxy with the
  system (and using the `systemctl` command).
- `galaxy_manage_errordocs` (default: `no`): Install Galaxy-styled 413 and 502 HTTP error documents for nginx. Requires
  write privileges for the nginx error document directory.
- `galaxy_manage_cleanup` (default: `no`): Install a cron job to clean up Galaxy framework and job execution temporary
  files. Requires `tmpwatch(8)` on RedHat-based systems or `tmpreaper(8)` on Debian-based systems. See the
  `galaxy_tmpclean_*` vars in the [defaults file][defaults] for details.

[client-build]: https://github.com/galaxyproject/galaxy/blob/dev/client/README.md#complete-client-build
[systemd]: https://www.freedesktop.org/wiki/Software/systemd/

**Galaxy code and configuration**

Options for configuring Galaxy and controlling which version is installed.

- `galaxy_config`: The contents of the Galaxy configuration file (`galaxy.ini` by default) are controlled by this
  variable. It is a hash of hashes (or dictionaries) that will be translated in to the configuration
  file. See the Example Playbooks below for usage.
- `galaxy_config_files`: List of hashes (with `src` and `dest` keys) of files to copy from the control machine. For example, to set job destinations, you can use the `galaxy_config_dir` variable followed by the file name as the `dest`, e.g. `dest: "{{ galaxy_config_dir }}/job_conf.xml"`. Make sure to add the appropriate setup within `galaxy_config` for each file added here (so, if adding `job_conf.xml` make sure that `galaxy_config.galaxy.job_config_file` points to that file).
- `galaxy_config_templates`: List of hashes (with `src` and `dest` keys) of templates to fill from the control machine.
- `galaxy_local_tools`: List of local tool files or directories to copy from the control machine, relative to
  `galaxy_local_tools_src_dir` (default: `files/galaxy/tools` in the playbook). List items can either be a tool
  filename, or a dictionary with keys `file`, `section_name`, and, optionally, `section_id`. If no `section_name` is
  specified, tools will be placed in a section named **Local Tools**.
- `galaxy_local_tools_dir`: Directory on the Galaxy server where local tools will be installed.
- `galaxy_dynamic_job_rules`: List of dynamic job rules to copy from the control machine, relative to
  `galaxy_dynamic_job_rules_src_dir` (default: `files/galaxy/dynamic_job_rules` in the playbook).
- `galaxy_dynamic_job_rules_dir` (default: `{{ galaxy_server_dir }}/lib/galaxy/jobs/rules`): Directory on the Galaxy
  server where dynamic job rules will be installed. If changed from the default, ensure the directory is on Galaxy's
  `$PYTHONPATH` (e.g. in `{{ galaxy_venv_dir }}/lib/python2.7/site-packages`) and configure the dynamic rules plugin in
  `job_conf.xml` accordingly.
- `galaxy_repo` (default: `https://github.com/galaxyproject/galaxy.git`): Upstream Git repository from which Galaxy
  should be cloned.
- `galaxy_commit_id` (default: `master`): A commit id, tag, branch, or other valid Git reference that Galaxy should be
  updated to. Specifying a branch will update to the latest commit on that branch. Using a real commit id is the only
  way to explicitly lock Galaxy at a specific version.
- `galaxy_force_checkout` (default: `no`): If `yes`, any modified files in the Galaxy repository will be discarded.
- `galaxy_clone_depth` (default: unset): Depth to use when performing git clone. Leave unspecified to clone entire
   history.

**Additional config files**

Some optional configuration files commonly used in production Galaxy servers can be configured from variables:

- `galaxy_dependency_resolvers`: Populate the `dependency_resolvers_conf.yml` file. See the [sample XML
  configuration][dependency_resolvers_conf_sample] for options.
- `galaxy_container_resolvers`: Populate the `container_resolvers_conf.yml` file. See the [sample XML
  configuration][container_resolvers_conf_sample] for options.
- `galaxy_job_metrics_plugins`: Populate the `job_metrics_conf.yml` file. See the [sample XML
  configuration][job_metrics_conf_sample] for options.

As of Galaxy 21.05 the sample configuration files for these features are in XML, but YAML is supported like so:

```yaml
galaxy_dependency_resolvers:
  - type: <XML tag name>
    <XML attribute name>: <XML attribute value>
```

For example:

```yaml
galaxy_dependency_resolvers:
  - type: galaxy_packages
  - type: conda
    prefix: /srv/galaxy/conda
    auto_init: true
    auto_install: false
```

[dependency_resolvers_conf_sample]: https://github.com/galaxyproject/galaxy/blob/release_21.05/lib/galaxy/config/sample/dependency_resolvers_conf.xml.sample
[container_resolvers_conf_sample]: https://github.com/galaxyproject/galaxy/blob/release_21.05/lib/galaxy/config/sample/container_resolvers_conf.xml.sample
[job_metrics_conf_sample]: https://github.com/galaxyproject/galaxy/blob/release_21.05/lib/galaxy/config/sample/job_metrics_conf.xml.sample

**Path configuration**

Options for controlling where certain Galaxy components are placed on the filesystem.

- `galaxy_venv_dir` (default: `<galaxy_server_dir>/.venv`): The role will create a [virtualenv][virtualenv] from which
  Galaxy will run, this controls where the virtualenv will be placed.
- `galaxy_virtualenv_command`: (default: `virtualenv`): The command used to create Galaxy's virtualenv. Set to `pyvenv`
  to use Python 3 on Galaxy >= 20.01.
- `galaxy_virtualenv_python`: (default: python of first `virtualenv` or `python` command on `$PATH`): The python binary
  to use when creating the virtualenv. For Galaxy < 20.01, use python2.7 (if it is not the default), for Galaxy >=
  20.01, use `python3.5` or higher.
- `galaxy_config_dir` (default: `<galaxy_server_dir>`): Directory that will be used for "static" configuration files.
- `galaxy_mutable_config_dir` (default: `<galaxy_server_dir>`): Directory that will be used for "mutable" configuration
  files, must be writable by the user running Galaxy.
- `galaxy_mutable_data_dir` (default: `<galaxy_server_dir>/database`): Directory that will be used for "mutable" data
  and caches, must be writable by the user running Galaxy.
- `galaxy_config_file` (default: `<galaxy_config_dir>/galaxy.ini`): Galaxy's primary configuration file.

**User management and privilege separation**

- `galaxy_separate_privileges` (default: `no`): Enable privilege separation mode.
- `galaxy_user` (default: user running ansible): The name of the system user under which Galaxy runs.
- `galaxy_privsep_user` (default: `root`): The name of the system user that owns the Galaxy code, config files, and
  virtualenv (and dependencies therein).
- `galaxy_group`: Common group between the Galaxy user and privilege separation user. If set and `galaxy_manage_paths`
  is enabled, directories containing potentially sensitive information such as the Galaxy config file will be created
  group- but not world-readable. Otherwise, directories are created world-readable.

**Access method control**

The role needs to perform tasks as different users depending on which features you have enabled and how you are
connecting to the target host. By default, the role will use `become` (i.e. sudo) to perform tasks as the appropriate
user if deemed necessary. Overriding this behavior is discussed in the [defaults file][defaults].

**systemd**

[systemd][systemd] is the standard system init daemon on most modern Linux flavors (and all of the ones supported by
this role). If `galaxy_manage_systemd` is enabled, a `galaxy` service will be configured in systemd to run Galaxy. This
service will be automatically started and configured to start when your system boots. You can control the Galaxy
service with the `systemctl` utility as the `root` user or with `sudo`:

```console
# systemctl start galaxy     # start galaxy
# systemctl reload galaxy    # attempt a "graceful" reload
# systemctl restart galaxy   # perform a hard restart
# systemctl stop galaxy      # stop galaxy
```

You can use systemd user mode if you do not have root privileges on your system by setting `galaxy_systemd_root` to
`false`. Add `--user` to the `systemctl` commands above to interact with systemd in user mode:

**Error documents**

- `galaxy_errordocs_dir`: Install Galaxy-styled HTTP 413 and 502 error documents under this directory. The 502 message
  uses nginx server side includes to allow administrators to create a custom message in `~/maint` when Galaxy is down.
  nginx must be configured separately to serve these error documents.
- `galaxy_errordocs_server_name` (default: Galaxy): used to display the message "`galaxy_errdocs_server_name` cannot be
  reached" on the 502 page.
- `galaxy_errordocs_prefix` (default: `/error`): Web-side path to the error document root.

**Miscellaneous options**

- `galaxy_admin_email_to`: If set, email this address when Galaxy has been updated. Assumes mail is properly configured
  on the managed host.
- `galaxy_admin_email_from`: Address to send the aforementioned email from.

Dependencies
------------

None

Example Playbook
----------------

### Basic ###

Install Galaxy on your local system with all the default options:

```yaml
- hosts: localhost
  vars:
    galaxy_server_dir: /srv/galaxy
  connection: local
  roles:
     - galaxyproject.galaxy
```

If your Ansible version >= 2.10.4, then when you run `ansible-playbook playbook.yml` you should supply an extra argument `-u $USER`, otherwise you will get an error.

Once installed, you can start with:

```console
$ cd /srv/galaxy
$ sh run.sh
```

### Best Practice ###

Install Galaxy as per the current production server best practices:

- Galaxy code (clone) is "clean": no configs or mutable data live underneath the clone
- Galaxy code and static configs are privilege separated: not owned/writeable by the user that runs Galaxy
- Configuration files are not world-readable
- PostgreSQL is used as the backing database
- The 18.01+ style YAML configuration is used
- Two [job handler mules][deployment-options] are started
- When the Galaxy code or configs are updated by Ansible, Galaxy will be restarted using `galaxyctl` or `systemctl restart galaxy-*`

[deployment-options]: https://docs.galaxyproject.org/en/master/admin/scaling.html#deployment-options

```yaml
- hosts: galaxyservers
  vars:
    galaxy_config_style: yaml
    galaxy_layout: root-dir
    galaxy_root: /srv/galaxy
    galaxy_commit_id: release_23.0
    galaxy_separate_privileges: yes
    galaxy_force_checkout: true
    galaxy_create_user: yes
    galaxy_manage_paths: yes
    galaxy_manage_systemd: yes
    galaxy_user: galaxy
    galaxy_privsep_user: gxpriv
    galaxy_group: galaxy
    postgresql_objects_users:
      - name: galaxy
        password: null
    postgresql_objects_databases:
      - name: galaxy
        owner: galaxy
    galaxy_config:
      gravity:
        process_manager: systemd
        galaxy_root: "{{ galaxy_root }}/server"
        galaxy_user: "{{ galaxy_user_name }}"
        virtualenv: "{{ galaxy_venv_dir }}"
        gunicorn:
          # listening options
          bind: "unix:{{ galaxy_mutable_config_dir }}/gunicorn.sock"
          # performance options
          workers: 2
          # Other options that will be passed to gunicorn
          # This permits setting of 'secure' headers like REMOTE_USER (and friends)
          # https://docs.gunicorn.org/en/stable/settings.html#forwarded-allow-ips
          extra_args: '--forwarded-allow-ips="*"'
          # This lets Gunicorn start Galaxy completely before forking which is faster.
          # https://docs.gunicorn.org/en/stable/settings.html#preload-app
          preload: true
        celery:
          concurrency: 2
          enable_beat: true
          enable: true
          queues: celery,galaxy.internal,galaxy.external
          pool: threads
          memory_limit: 2
          loglevel: DEBUG
        handlers:
          handler:
            processes: 2
            pools:
              - job-handlers
              - workflow-schedulers
      galaxy:
        database_connection: "postgresql:///galaxy?host=/var/run/postgresql"
  pre_tasks:
    - name: Install Dependencies
      apt:
        name:
          - sudo
          - git
          - make
          - python3-venv
          - python3-setuptools
          - python3-dev
          - python3-psycopg2
          - gcc
          - acl
          - gnutls-bin
          - libmagic-dev
      become: yes
  roles:
    # Install with:
    #   % ansible-galaxy install galaxyproject.postgresql
    - role: galaxyproject.postgresql
      become: yes
    # Install with:
    #   % ansible-galaxy install natefoo.postgresql_objects
    - role: galaxyproject.postgresql_objects
      become: yes
      become_user: postgres
    - role: galaxyproject.galaxy
```

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

This role was written and contributed to by the following people:

- [Enis Afgan](https://github.com/afgane)
- [Dannon Baker](https://github.com/dannon)
- [Simon Belluzzo](https://github.com/simonalpha)
- [John Chilton](https://github.com/jmchilton)
- [Nate Coraor](https://github.com/natefoo)
- [Helena Rasche](https://github.com/hexylena)
- [Mira Kuntz](https://github.com/mira-miracoli)
