"""
Vultr Cloud Module
==================

.. versionadded:: 2016.3.0

The Vultr cloud module is used to control access to the Vultr VPS system.

Use of this module only requires the ``api_key`` parameter.

Set up the cloud configuration at ``/etc/salt/cloud.providers`` or
``/etc/salt/cloud.providers.d/vultr.conf``:

.. code-block:: yaml

    my-vultr-config:
      # Vultr account api key
      api_key: <supersecretapi_key>
      driver: vultr

Set up the cloud profile at ``/etc/salt/cloud.profiles`` or
``/etc/salt/cloud.profiles.d/vultr.conf``:

.. code-block:: yaml

    nyc-4gb-4cpu-ubuntu-14-04:
      location: 1
      provider: my-vultr-config
      image: 160
      size: 95
      enable_private_network: True

This driver also supports Vultr's `startup script` feature.  You can list startup
scripts in your account with

.. code-block:: bash

    salt-cloud -f list_scripts <name of vultr provider>

That list will include the IDs of the scripts in your account.  Thus, if you
have a script called 'setup-networking' with an ID of 493234 you can specify
that startup script in a profile like so:

.. code-block:: yaml

    nyc-2gb-1cpu-ubuntu-17-04:
      location: 1
      provider: my-vultr-config
      image: 223
      size: 13
      startup_script_id: 493234

Similarly you can also specify a fiewall group ID using the option firewall_group_id. You can list
firewall groups with

.. code-block:: bash

    salt-cloud -f list_firewall_groups <name of vultr provider>

To specify SSH keys to be preinstalled on the server, use the ssh_key_names setting

.. code-block:: yaml

    nyc-2gb-1cpu-ubuntu-17-04:
      location: 1
      provider: my-vultr-config
      image: 223
      size: 13
      ssh_key_names: dev1,dev2,salt-master

You can list SSH keys available on your account using

.. code-block:: bash

    salt-cloud -f list_keypairs <name of vultr provider>

When using a custom image type (such as when you are installing from an ISO),
you may specify ``ssh_username`` and ``password`` to be used by Salt to saltify
the instance. You may also specify ``isoid`` to use select either a publicly-
available ISO image or a custom ISO image present in your account; additionally
you can define ``ipxe_chain_url`` to specifiy the URL of an iPXE-compatible
script to chainload.

.. versionadded:: 3004.0

.. code-block:: yaml

    tor-1gb-1cpu-custom:
      location: 22
      provider: my-vultr-config
      image: 159
      size: 201
      ssh_username: 'root'
      password: 'CorrectHorseBatteryStaple'
      isoid: 641216
      ipxe_chain_url: 'https://some.example.com/script.ipxe'

You can list account-level ISO images with

.. code-block:: bash

    salt-cloud -f list_acct_isos <name of vultr provider>

and public ISO images with

.. code-block:: bash

    salt-cloud -f list_public_isos <name of vultr provider>

You may pass metadata using Vultr's metadata service to your instance by setting
either ``userdata`` or ``userdata_file``. The value for ``userdata`` can be a
string or a path to a file, in which case you can also optionally specify
``userdata_template``, which sets the renderer to render the file with:

.. code-block:: yaml

    ams-64gb-16cpu-centos-8:
      location: 7
      provider: my-vultr-config
      image: 362
      size: 207
      userdata: /srv/scripts/userdata.tmpl
      userdata_template: jinja

"""

import base64
import logging
import os.path
import pprint
import time
import urllib.parse

import salt.config as config
import salt.utils.files
import salt.utils.stringutils
from salt.exceptions import SaltCloudConfigError, SaltCloudSystemExit

try:
    import validators

    HAS_VALIDATORS = True
except ImportError:
    HAS_VALIDATORS = False

# Get logging started
log = logging.getLogger(__name__)

__virtualname__ = "vultr"

DETAILS = {}


def __virtual__():
    """
    Set up the Vultr functions and check for configurations
    """
    if get_configured_provider() is False:
        return False

    return __virtualname__


def get_dependencies():
    """
    Warn if dependencies aren't met.
    """
    deps = {
        "validators": HAS_VALIDATORS,
    }
    return config.check_driver_dependencies(__virtualname__, deps)


def get_configured_provider():
    """
    Return the first configured instance.
    """
    return config.is_provider_configured(
        __opts__, __active_provider_name__ or "vultr", ("api_key",)
    )


def _cache_provider_details(conn=None):
    """
    Provide a place to hang onto results of --list-[locations|sizes|images]
    so we don't have to go out to the API and get them every time.
    """
    DETAILS["avail_locations"] = {}
    DETAILS["avail_sizes"] = {}
    DETAILS["avail_images"] = {}
    locations = avail_locations(conn)
    images = avail_images(conn)
    sizes = avail_sizes(conn)

    for key, location in locations.items():
        DETAILS["avail_locations"][location["name"]] = location
        DETAILS["avail_locations"][key] = location

    for key, image in images.items():
        DETAILS["avail_images"][image["name"]] = image
        DETAILS["avail_images"][key] = image

    for key, vm_size in sizes.items():
        DETAILS["avail_sizes"][vm_size["name"]] = vm_size
        DETAILS["avail_sizes"][key] = vm_size


def avail_locations(conn=None):
    """
    Return available datacenter locations.

    CLI Example:

    .. code-block:: bash

        salt-cloud --list-locations my-vultr-config
    """
    return _query("regions/list")


def avail_scripts(conn=None):
    """
    Return list of available startup scripts.
    """
    return _query("startupscript/list")


def avail_acct_isos(conn=None):
    """
    Return list of available ISO images in account.

    .. versionadded:: 3004.0

    """
    return _query("iso/list")


def list_acct_isos(conn=None, call=None):
    """
    Return list of available ISO images in account.

    .. versionadded:: 3004.0

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_acct_isos my-vultr-config
    """
    return avail_acct_isos()


def avail_public_isos(conn=None):
    """
    Return list of available public ISO images.

    .. versionadded:: 3004.0
    
    """
    return _query("iso/list_public")


def list_public_isos(conn=None, call=None):
    """
    .. versionadded:: 3004.0

    Return list of available public ISO images.

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_public_isos my-vultr-config
    """
    return avail_public_isos()


def avail_firewall_groups(conn=None):
    """
    Return available firewall groups.

    .. versionadded:: 3004.0

    """
    return _query("firewall/group_list")


def avail_keys(conn=None):
    """
    Return list of available SSH keys.

    .. versionadded:: 3004.0
    
    """
    return _query("sshkey/list")


def list_scripts(conn=None, call=None):
    """
    Return list of startup scripts.

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_scripts my-vultr-config
    """
    return avail_scripts()


def list_firewall_groups(conn=None, call=None):
    """
    Return list of firewall groups.

    .. versionadded:: 3004.0

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_firewall_groups my-vultr-config
    """
    return avail_firewall_groups()


def list_keypairs(conn=None, call=None):
    """
    Return list of SSH keys.

    .. versionadded:: 3004.0

    CLI Example:

    .. code-block:: bash

        salt-cloud -f list_keypairs my-vultr-config
    """
    return avail_keys()


def show_keypair(kwargs=None, call=None):
    """
    Return list of SSH keys.

    .. versionadded:: 3004.0

    keyname
        The SSHKEYID of the key to be shown.

    CLI Example:

    .. code-block:: bash

        salt-cloud -f show_keypair my-vultr-config keyname="6043ec83f126a"
    """
    if not kwargs:
        kwargs = {}

    if "keyname" not in kwargs:
        log.error("A keyname is required.")
        return False

    keys = list_keypairs(call="function")
    keyid = keys[kwargs["keyname"]]["SSHKEYID"]
    log.debug("Key ID is %s", keyid)

    return keys[kwargs["keyname"]]


def avail_sizes(conn=None):
    """
    Return available sizes ("plans").

    CLI Example:

    .. code-block:: bash

        salt-cloud --list-sizes my-vultr-config
    """
    return _query("plans/list")


def avail_images(conn=None):
    """
    Return available images.

    CLI Example:

    .. code-block:: bash

        salt-cloud --list-images my-vultr-config
    """
    return _query("os/list")


def list_nodes(**kwargs):
    """
    Returns a list of nodes ("instances"), keeping only a brief listing.

    CLI Example:

    .. code-block:: bash

        salt-cloud -Q
        salt-cloud --query
        salt-cloud -f list_nodes my-vultr-config
    """
    ret = {}

    nodes = list_nodes_full()
    for node in nodes:
        ret[node] = {}
        for prop in "id", "image", "size", "state", "private_ips", "public_ips":
            ret[node][prop] = nodes[node][prop]

    return ret


def list_nodes_full(**kwargs):
    """
    List nodes ("instances"), with all available information.

    CLI Example:

    .. code-block:: bash

        salt-cloud -F
        salt-cloud --full-query
        salt-cloud -f list_nodes_full my-vultr-config
    """
    nodes = _query("server/list")
    ret = {}

    for node in nodes:
        name = nodes[node]["label"]
        ret[name] = nodes[node].copy()
        ret[name]["id"] = node
        ret[name]["image"] = nodes[node]["os"]
        ret[name]["size"] = nodes[node]["VPSPLANID"]
        ret[name]["state"] = nodes[node]["status"]
        ret[name]["private_ips"] = nodes[node]["internal_ip"]
        ret[name]["public_ips"] = nodes[node]["main_ip"]

    return ret


def list_nodes_select(conn=None, call=None):
    """
    Return a list of the nodes ("instances"), with selected
    fields.

    CLI Examples:

    .. code-block:: bash

        salt-cloud -S my-vultr-config
    """
    return __utils__["cloud.list_nodes_select"](
        list_nodes_full(), __opts__["query.selection"], call,
    )


def destroy(name):
    """
    Destroys a node ("instance") by name. Either a name or a SUBID must
    be provided.

    name
        The name of node to be destroyed.

    CLI Example:

    .. code-block:: bash

        salt-cloud -d node_name
    """
    node = show_instance(name, call="action")
    params = {"SUBID": node["SUBID"]}
    result = _query(
        "server/destroy",
        method="POST",
        decode=False,
        data=urllib.parse.urlencode(params),
    )

    # The return of a destroy call is empty in the case of a success.
    # Errors are only indicated via HTTP status code. Status code 200
    # effetively therefore means "success".
    if result.get("body") == "" and result.get("text") == "":
        return True
    return result


def stop(*args, **kwargs):
    """
    Execute a "stop" action on a node ("instance"). Either a name or a SUBID must
    be provided.

    name
        The name of the node to stop.

    CLI Example:

    .. code-block:: bash

        salt-cloud -a stop node_name
    """
    return _query("server/halt")


def start(*args, **kwargs):
    """
    Execute a "start" action on a node ("instance"). Either a name or a SUBID must
    be provided.

    name
        The name of the node to start. 

    CLI Example:

    .. code-block:: bash

        salt-cloud -a stop node_name
    """
    return _query("server/start")


def show_instance(name, call=None):
    """
    Displays details about a particular instance. Either a name or a SUBID must
    be provided.

    name
        The name of the node for which to display details.

    CLI Example:

    .. code-block:: bash

        salt-cloud -a show_instance node_name
    """
    if call != "action":
        raise SaltCloudSystemExit(
            "The show_instance action must be called with -a or --action."
        )

    nodes = list_nodes_full()
    # Find under which cloud service the name is listed, if any
    if name not in nodes:
        return {}
    __utils__["cloud.cache_node"](nodes[name], __active_provider_name__, __opts__)
    return nodes[name]


def _lookup_vultrid(which_key, availkey, keyname):
    """
    Helper function to retrieve a Vultr ID
    """
    if DETAILS == {}:
        _cache_provider_details()

    which_key = str(which_key)
    try:
        return DETAILS[availkey][which_key][keyname]
    except KeyError:
        return False


def create(vm_):
    """
    Create a single instance from a data dict.

    CLI Examples:

    .. code-block:: bash

        salt-cloud -p nyc-4gb-4cpu-ubuntu-14-04 host1
        salt-cloud -m /path/to/mymap.sls -P
    """
    if "driver" not in vm_:
        vm_["driver"] = vm_["provider"]

    private_networking = config.get_cloud_config_value(
        "enable_private_network", vm_, __opts__, search_global=False, default=False,
    )

    ssh_username = config.get_cloud_config_value(
        "ssh_username", vm_, __opts__, search_global=False, default=False,
    )

    password = config.get_cloud_config_value(
        "password", vm_, __opts__, search_global=False, default=False,
    )

    ssh_key_ids = config.get_cloud_config_value(
        "ssh_key_names", vm_, __opts__, search_global=False, default=None
    )

    startup_script = config.get_cloud_config_value(
        "startup_script_id", vm_, __opts__, search_global=False, default=None,
    )

    isoid = config.get_cloud_config_value(
        "isoid", vm_, __opts__, search_global=False, default=None,
    )

    if startup_script and str(startup_script) not in avail_scripts():
        log.error(
            "Your Vultr account does not have a startup script with ID %s",
            str(startup_script),
        )
        return False

    if (
        isoid
        and str(isoid) not in avail_acct_isos()
        and str(isoid) not in avail_public_isos()
    ):
        log.error(
            "Your Vultr account does not have an ISO image with ID %s and it does not match a public ISO image",
            str(isoid),
        )
        return False

    ipxe_chain_url = config.get_cloud_config_value(
        "ipxe_chain_url", vm_, __opts__, search_global=False, default=False,
    )

    if ipxe_chain_url and not validators.url(str(ipxe_chain_url)):
        log.error(
            "iPXE Chain URL '%s' is malformed", str(ipxe_chain_url),
        )
        return False

    userdata = config.get_cloud_config_value(
        "userdata", vm_, __opts__, search_global=False, default=None
    )
    userdata_template = config.get_cloud_config_value(
        "userdata_template", vm_, __opts__, search_global=False, default=None
    )

    firewall_group_id = config.get_cloud_config_value(
        "firewall_group_id", vm_, __opts__, search_global=False, default=None,
    )

    if firewall_group_id and str(firewall_group_id) not in avail_firewall_groups():
        log.error(
            "Your Vultr account does not have a firewall group with ID %s",
            str(firewall_group_id),
        )
        return False

    if ssh_key_ids is not None:
        key_list = ssh_key_ids.split(",")
        available_keys = avail_keys()
        for key in key_list:
            if key and str(key) not in available_keys:
                log.error("Your Vultr account does not have a key with ID %s", str(key))
                return False

    if private_networking is not None:
        if not isinstance(private_networking, bool):
            raise SaltCloudConfigError(
                "'private_networking' should be a boolean value."
            )
    if private_networking is True:
        enable_private_network = "yes"
    else:
        enable_private_network = "no"

    __utils__["cloud.fire_event"](
        "event",
        "starting create",
        "salt/cloud/{}/creating".format(vm_["name"]),
        args=__utils__["cloud.filter_event"](
            "creating", vm_, ["name", "profile", "provider", "driver"]
        ),
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )

    osid = _lookup_vultrid(vm_["image"], "avail_images", "OSID")
    if not osid:
        log.error("Vultr does not have an image with id or name %s", vm_["image"])
        return False

    vpsplanid = _lookup_vultrid(vm_["size"], "avail_sizes", "VPSPLANID")
    if not vpsplanid:
        log.error("Vultr does not have a size with id or name %s", vm_["size"])
        return False

    dcid = _lookup_vultrid(vm_["location"], "avail_locations", "DCID")
    if not dcid:
        log.error("Vultr does not have a location with id or name %s", vm_["location"])
        return False

    kwargs = {
        "label": vm_["name"],
        "OSID": osid,
        "VPSPLANID": vpsplanid,
        "DCID": dcid,
        "hostname": vm_["name"],
        "enable_private_network": enable_private_network,
    }
    if startup_script:
        kwargs["SCRIPTID"] = startup_script

    if isoid:
        kwargs["ISOID"] = isoid

    if ipxe_chain_url:
        kwargs["ipxe_chain_url"] = ipxe_chain_url

    if userdata is not None and os.path.isfile(userdata):
        try:
            with __utils__["files.fopen"](userdata, "r") as fp_:
                kwargs["userdata"] = __utils__["cloud.userdata_template"](
                    __opts__, vm_, fp_.read()
                )
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Failed to read userdata from %s: %s", userdata, exc)

    if userdata is not None:
        try:
            kwargs["userdata"] = base64.b64encode(
                salt.utils.stringutils.to_bytes(userdata)
            )
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Failed to encode userdata: %s", exc)

    if firewall_group_id:
        kwargs["FIREWALLGROUPID"] = firewall_group_id

    if ssh_key_ids:
        kwargs["SSHKEYID"] = ssh_key_ids

    log.info("Creating Cloud VM %s", vm_["name"])

    __utils__["cloud.fire_event"](
        "event",
        "requesting instance",
        "salt/cloud/{}/requesting".format(vm_["name"]),
        args={
            "kwargs": __utils__["cloud.filter_event"](
                "requesting", kwargs, list(kwargs)
            ),
        },
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )

    try:
        data = _query(
            "server/create", method="POST", data=urllib.parse.urlencode(kwargs)
        )
        if int(data.get("status", "200")) >= 300:
            log.error(
                "Error creating %s on Vultr\n\n" "Vultr API returned %s\n",
                vm_["name"],
                data,
            )
            log.error(
                "Status 412 may mean that you are requesting an\n"
                "invalid location, image, or size."
            )

            __utils__["cloud.fire_event"](
                "event",
                "instance request failed",
                "salt/cloud/{}/requesting/failed".format(vm_["name"]),
                args={"kwargs": kwargs},
                sock_dir=__opts__["sock_dir"],
                transport=__opts__["transport"],
            )
            return False
    except Exception as exc:  # pylint: disable=broad-except
        log.error(
            "Error creating %s on Vultr\n\n"
            "The following exception was thrown when trying to "
            "run the initial deployment:\n%s",
            vm_["name"],
            exc,
            # Show the traceback if the debug logging level is enabled
            exc_info_on_loglevel=logging.DEBUG,
        )
        __utils__["cloud.fire_event"](
            "event",
            "instance request failed",
            "salt/cloud/{}/requesting/failed".format(vm_["name"]),
            args={"kwargs": kwargs},
            sock_dir=__opts__["sock_dir"],
            transport=__opts__["transport"],
        )
        return False

    def wait_for_hostname():
        """
        Wait for the IP address to become available
        """
        data = show_instance(vm_["name"], call="action")
        log.debug("Waiting for IP address to become available")
        main_ip = str(data.get("main_ip", "0"))
        if main_ip.startswith("0"):
            time.sleep(3)
            return False
        return data["main_ip"]

    def wait_for_default_password():
        """
        Wait for the IP address to become available
        """
        data = show_instance(vm_["name"], call="action")
        log.debug("Waiting for default password")
        default_password = str(data.get("default_password", ""))
        if default_password == "" or default_password == "not supported":
            time.sleep(1)
            return False
        return data["default_password"]

    def wait_for_status():
        """
        Wait for the IP address to become available
        """
        data = show_instance(vm_["name"], call="action")
        log.debug("Waiting for status normal")
        if str(data.get("status", "")) != "active":
            time.sleep(1)
            return False
        return data["default_password"]

    def wait_for_server_state():
        """
        Wait for the IP address to become available
        """
        data = show_instance(vm_["name"], call="action")
        log.debug("Waiting for server state ok")
        if str(data.get("server_state", "")) != "ok":
            time.sleep(1)
            return False
        return data["default_password"]

    vm_["ssh_host"] = __utils__["cloud.wait_for_fun"](
        wait_for_hostname,
        timeout=config.get_cloud_config_value(
            "wait_for_fun_timeout", vm_, __opts__, default=15 * 60
        ),
    )
    if ssh_username:
        vm_["ssh_username"] = ssh_username
    if not password:
        vm_["password"] = __utils__["cloud.wait_for_fun"](
            wait_for_default_password,
            timeout=config.get_cloud_config_value(
                "wait_for_fun_timeout", vm_, __opts__, default=15 * 60
            ),
        )
    else:
        vm_["password"] = password
    __utils__["cloud.wait_for_fun"](
        wait_for_status,
        timeout=config.get_cloud_config_value(
            "wait_for_fun_timeout", vm_, __opts__, default=15 * 60
        ),
    )
    __utils__["cloud.wait_for_fun"](
        wait_for_server_state,
        timeout=config.get_cloud_config_value(
            "wait_for_fun_timeout", vm_, __opts__, default=15 * 60
        ),
    )

    __opts__["hard_timeout"] = config.get_cloud_config_value(
        "hard_timeout",
        get_configured_provider(),
        __opts__,
        search_global=False,
        default=None,
    )

    # Bootstrap
    ret = __utils__["cloud.bootstrap"](vm_, __opts__)

    ret.update(show_instance(vm_["name"], call="action"))

    log.info("Created Cloud VM '%s'", vm_["name"])
    log.debug("'%s' VM creation details:\n%s", vm_["name"], pprint.pformat(data))

    __utils__["cloud.fire_event"](
        "event",
        "created instance",
        "salt/cloud/{}/created".format(vm_["name"]),
        args=__utils__["cloud.filter_event"](
            "created", vm_, ["name", "profile", "provider", "driver"]
        ),
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )

    return ret


def _query(path, method="GET", data=None, params=None, header_dict=None, decode=True):
    """
    Perform a query directly against the Vultr REST API
    """
    api_key = config.get_cloud_config_value(
        "api_key", get_configured_provider(), __opts__, search_global=False,
    )
    management_host = config.get_cloud_config_value(
        "management_host",
        get_configured_provider(),
        __opts__,
        search_global=False,
        default="api.vultr.com",
    )
    url = "https://{management_host}/v1/{path}?api_key={api_key}".format(
        management_host=management_host, path=path, api_key=api_key,
    )

    if header_dict is None:
        header_dict = {}

    result = __utils__["http.query"](
        url,
        method=method,
        params=params,
        data=data,
        header_dict=header_dict,
        port=443,
        text=True,
        decode=decode,
        decode_type="json",
        hide_fields=["api_key"],
        opts=__opts__,
    )
    if "dict" in result:
        return result["dict"]

    return result
