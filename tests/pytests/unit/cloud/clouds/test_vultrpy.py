"""
    :codeauthor: Gary T. Giesen <ggiesen@giesen.me>
"""

import pytest
import salt.cloud.clouds.vultrpy as vultr
from tests.support.mock import MagicMock, patch


class ModelMock(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = MagicMock()
        self.model.__slots__ = list(self)

        for attr, value in self.items():
            setattr(self, attr, value)


@pytest.fixture
def default_kwargs():
    return {
        "api_key": "OUCHEZAEKAISEIQUAIFIE0EEC6THOHKEI7AX",
    }


@pytest.fixture
def locations():
    return {
        "1": {
            "DCID": "1",
            "name": "New Jersey",
            "country": "US",
            "continent": "North America",
            "state": "NJ",
            "ddos_protection": True,
            "block_storage": True,
            "regioncode": "EWR",
        },
        "7": {
            "DCID": "7",
            "name": "Amsterdam",
            "country": "NL",
            "continent": "Europe",
            "state": "",
            "ddos_protection": True,
            "block_storage": False,
            "regioncode": "AMS",
        },
        "22": {
            "DCID": "22",
            "name": "Toronto",
            "country": "CA",
            "continent": "North America",
            "state": "",
            "ddos_protection": False,
            "block_storage": False,
            "regioncode": "YTO",
        },
    }


@pytest.fixture
def sizes():
    return {
        "115": {
            "VPSPLANID": "115",
            "name": "8192 MB RAM,110 GB SSD,10.00 TB BW",
            "vcpu_count": "2",
            "ram": "8192",
            "disk": "110",
            "bandwidth": "10.00",
            "bandwidth_gb": "10240",
            "price_per_month": "60.00",
            "plan_type": "DEDICATED",
            "windows": False,
            "available_locations": [1],
        },
        "201": {
            "VPSPLANID": "201",
            "name": "1024 MB RAM,25 GB SSD,1.00 TB BW",
            "vcpu_count": "1",
            "ram": "1024",
            "disk": "25",
            "bandwidth": "1.00",
            "bandwidth_gb": "1024",
            "price_per_month": "5.00",
            "plan_type": "SSD",
            "windows": False,
            "available_locations": [1, 7, 22],
        },
        "203": {
            "VPSPLANID": "203",
            "name": "4096 MB RAM,80 GB SSD,3.00 TB BW",
            "vcpu_count": "2",
            "ram": "4096",
            "disk": "80",
            "bandwidth": "3.00",
            "bandwidth_gb": "3072",
            "price_per_month": "20.00",
            "plan_type": "SSD",
            "windows": False,
            "available_locations": [1, 7, 22],
        },
        "400": {
            "VPSPLANID": "400",
            "name": "1024 MB RAM,32 GB SSD,1.00 TB BW",
            "vcpu_count": "1",
            "ram": "1024",
            "disk": "32",
            "bandwidth": "1.00",
            "bandwidth_gb": "1024",
            "price_per_month": "6.00",
            "plan_type": "HIGHFREQUENCY",
            "windows": False,
            "available_locations": [1, 7, 22],
        },
        "401": {
            "VPSPLANID": "401",
            "name": "2048 MB RAM,64 GB SSD,2.00 TB BW",
            "vcpu_count": "1",
            "ram": "2048",
            "disk": "64",
            "bandwidth": "2.00",
            "bandwidth_gb": "2048",
            "price_per_month": "12.00",
            "plan_type": "HIGHFREQUENCY",
            "windows": False,
            "available_locations": [1, 7, 22],
        },
    }


@pytest.fixture
def images():
    return {
        "362": {
            "OSID": 362,
            "name": "CentOS 8 x64",
            "arch": "x64",
            "family": "centos",
            "windows": False,
        },
        "240": {
            "OSID": 240,
            "name": "Windows 2016 x64",
            "arch": "x64",
            "family": "windows",
            "windows": True,
        },
        "159": {
            "OSID": 159,
            "name": "Custom",
            "arch": "x64",
            "family": "iso",
            "windows": False,
        },
        "164": {
            "OSID": 164,
            "name": "Snapshot",
            "arch": "x64",
            "family": "snapshot",
            "windows": False,
        },
        "180": {
            "OSID": 180,
            "name": "Backup",
            "arch": "x64",
            "family": "backup",
            "windows": False,
        },
        "186": {
            "OSID": 186,
            "name": "Application",
            "arch": "x64",
            "family": "application",
            "windows": False,
        },
        "426": {
            "OSID": 426,
            "name": "Marketplace App",
            "arch": "x64",
            "family": "marketplace_app",
            "windows": False,
        },
    }


@pytest.fixture
def scripts():
    return {
        "793055": {
            "SCRIPTID": "793055",
            "date_created": "2021-03-06 20:43:10",
            "date_modified": "2021-03-06 20:43:10",
            "name": "boot",
            "type": "boot",
            "script": "#!/bin/sh\n\n\n# NOTE: This is an example that sets up SSH authorization. To use it, you'd need to replace \"ssh-rsa AA... youremail@example.com\" with your SSH public.\n# You can replace this entire script with anything you'd like, there is no need to keep it\n\n\nmkdir -p /root/.ssh\nchmod 600 /root/.ssh\necho ssh-rsa AA... youremail@example.com > /root/.ssh/authorized_keys\nchmod 700 /root/.ssh/authorized_keys",
            "v2_id": "5c4f015c-6b19-44d2-8b2a-3340b01a06ee",
        },
        "793056": {
            "SCRIPTID": "793056",
            "date_created": "2021-03-06 20:43:25",
            "date_modified": "2021-03-06 20:43:25",
            "name": "pxe",
            "type": "pxe",
            "script": '#!ipxe\n# NOTE: This is an example that boots CoreOS. You\'d need to add your SSH key before this would work\n\nset base-url http://stable.release.core-os.net/amd64-usr/current\n\nkernel ${base-url}/coreos_production_pxe.vmlinuz sshkey="ssh-rsa AAAA..." cloud-config-url=http://169.254.169.254/2014-09-12/coreos-init\ninitrd ${base-url}/coreos_production_pxe_image.cpio.gz\nboot',
            "v2_id": "74c44016-c1e9-4339-b4f5-ff000692803c",
        },
    }


@pytest.fixture
def acct_isos():
    return {
        "591272": {
            "ISOID": 591272,
            "date_created": "2019-05-14 19:57:18",
            "filename": "CentOS-7-x86_64-DVD-1810.iso",
            "size": 4588568576,
            "md5sum": "5b61d5b378502e9cba8ba26b6696c92a",
            "sha512sum": "332cfc3593b091ac0e157a800fb1c1599f9f72e69441e46b50ed84f5ab053b7681ebf4ed660a6a8bfccbf8e3ae9266e3c6016f08439fc36e157ef7aa8be7b14a",
            "status": "complete",
            "v2_id": "3f86bcf6-9235-4ecc-bd4a-63f8ce7a5967",
        },
        "800882": {
            "ISOID": 800882,
            "date_created": "2020-09-15 22:39:40",
            "filename": "CentOS-8.2.2004-x86_64-dvd1.iso",
            "size": 8231321600,
            "md5sum": "47dc26d76e566280cc47437fd2466134",
            "sha512sum": "ff1164dc26ba47616f2b26a18158398a7d7930487770a8bb9e573d5758e01255ebc11db68c22976abe684a857083a0fae445e9d41d11a24a2073cdb1b500ae9a",
            "status": "complete",
            "v2_id": "ef4d7479-0def-4706-ac88-5f30e7376c61",
        },
    }


@pytest.fixture
def public_isos():
    return {
        "417366": {
            "ISOID": 417366,
            "name": "Ubuntu 18.04",
            "description": "18.04 x86_64",
            "v2_id": "0eaece5e-6e59-4ef8-8b84-28f4d4c11fb0",
        },
        "641216": {
            "ISOID": 641216,
            "name": "CentOS 8 x86_64",
            "description": "CentOS-8-x86_64-1905-dvd1.iso",
            "v2_id": "e5c23c48-08e4-4e46-9895-cb8faf2a934e",
        },
        "802022": {
            "ISOID": 802022,
            "name": "SystemRescueCD",
            "description": "6.1.8",
            "v2_id": "985a68c7-061e-4668-93c2-5e898920d224",
        },
    }


@pytest.fixture
def keys():
    return {
        "6043ec83f126a": {
            "SSHKEYID": "6043ec83f126a",
            "date_created": "2021-03-06 20:56:35",
            "name": "ed25519 SSH Key",
            "ssh_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN1VVfN6mpiKlq5Es9mkdEtKQMblP3EkegEI3dHIIXcK ed25519 SSH Key",
            "v2_id": "121549dd-d43a-47fb-b87f-9a09afef8680",
        },
        "6043eccc2800d": {
            "SSHKEYID": "6043eccc2800d",
            "date_created": "2021-03-06 20:57:48",
            "name": "rsa-4096 SSH Key",
            "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDvsiMM+F0JBcCrKDDwoSXCkLOj5BR/Vku3Yq9ssQcHZ2t41kop1Dn/KNIT8mwzSQHG6EfojAteSEnqqU1LRqhmrctzYHwGKpJSz+eBLqeS7SXgviZmtHtnx79PzxD+5bgJu6J/VvMU0s3pKvPwS70Ede0eQtyKGOYKnR10Ix3jS3Kna1HWZusjX80AsPpWM9fvQ7qrUAQh5RKKrOuK9Y02qayPcvERN2roM71YZoTnNiAEhkf52AqUOdDOzN2SIzcmzffpx6KPZgBVVWvyWNTkv7WGbbp6NEHmnhJZFDnX+jaobaKjHKmDCGp3bidIU+XpMJYRBvJQGsTuRVJWzYRLLBavBD82CvY+rU8TIqxPGtRi7V6YVDolI6g9Ff3ofXFySZYpuC3h7EzVHtAHHqiT/GPBfXQRFztLrWVdqmPuyYjAl6lVyeR+egtKtF0HWnm8VXEbObDpzGMVhztEJ3Hl4NO43tXBLHgRvVukLjsF1VSFsDm9Hk5DPim9oo6ZSo5PZCGtgEV4PfY5M3b8Qmfp7uiQINZ0b9D6hcEaGsqqLPQrYTrbkl3PhmI8NVdpc03nMLUwlMiYQ9lde4x+0+oN2ZPOmIt7zq0O+2vQNsbTpMo8zluU0aeQ06lT43qyrNyN/MmVTIo3sGEBP+woUKE5aPv6M/UMtf/cYVWrRPVvKQ== rsa-4096 SSH Key",
            "v2_id": "14b57e84-4a55-45c3-842f-5721c84f9096",
        },
    }


@pytest.fixture
def firewall_groups():
    return {
        "2aac0c5f": {
            "FIREWALLGROUPID": "2aac0c5f",
            "description": "group1",
            "date_created": "2021-03-06 21:12:28",
            "date_modified": "2021-03-06 21:12:28",
            "instance_count": 0,
            "rule_count": 0,
            "max_rule_count": 50,
            "v2_id": "d16c5836-ffc3-4478-b9c0-76175dd507f9",
        },
        "ef8d7e3c": {
            "FIREWALLGROUPID": "ef8d7e3c",
            "description": "group2",
            "date_created": "2021-03-06 21:12:44",
            "date_modified": "2021-03-06 21:12:44",
            "instance_count": 0,
            "rule_count": 0,
            "max_rule_count": 50,
            "v2_id": "c842dcf0-5d42-49d0-a8ff-8edd16b5c9e7",
        },
    }


@pytest.fixture
def nodes():
    return {
        "host1.example.com": {
            "id": "42164666",
            "image": "Custom Installed",
            "size": "201",
            "state": "active",
            "private_ips": "",
            "public_ips": "192.0.2.143",
        },
        "host2.example.com": {
            "id": "35968667",
            "image": "CentOS SELinux 8 x64",
            "size": "203",
            "state": "active",
            "private_ips": "",
            "public_ips": "198.51.100.226",
        },
    }


@pytest.fixture
def nodes_full():
    return {
        "host1.example.com": {
            "SUBID": "42164666",
            "os": "Custom Installed",
            "ram": "1024 MB",
            "disk": "Virtual 25 GB",
            "main_ip": "192.0.2.143",
            "vcpu_count": "1",
            "location": "Amsterdam",
            "DCID": "7",
            "default_password": "c0Jkwj(p;&?4sY5Y",
            "date_created": "2020-04-20 13:20:00",
            "pending_charges": "1.12",
            "status": "active",
            "cost_per_month": "5.00",
            "current_bandwidth_gb": 1.046,
            "allowed_bandwidth_gb": "1000",
            "netmask_v4": "255.255.255.0",
            "gateway_v4": "192.0.2.1",
            "power_status": "running",
            "server_state": "ok",
            "VPSPLANID": "201",
            "v6_main_ip": "2001:db8:5001:dead:5400:03ff:fe10:9a81",
            "v6_network_size": "64",
            "v6_network": "2001:db8:5001:dead::",
            "v6_networks": [
                {
                    "v6_main_ip": "2001:db8:5001:dead:5400:03ff:fe10:9a81",
                    "v6_network_size": "64",
                    "v6_network": "2001:db8:5001:dead::",
                }
            ],
            "label": "host1.example.com",
            "internal_ip": "",
            "kvm_url": "https://my.vultr.com/subs/vps/novnc/api.php?data=ojee6EP2Ohquom7el7cah2be1ize8phah7ahNo7Hoh8beivahNum3quee6aiSaek5quai2aechaiQuo-ahmie7eiNaephiela1Aagh-Ieched8ieXaijiaqueLah0reiQuukieMaeBahphut3pee7vieyah5woh5iiWae0rooquie8waejiexaeM6EiHaethooRu3pieYuphaesh0queiM1Phie3eWai1chair9ut7oaga6eikahlein6ooXayee1owi5aeMij1",
            "auto_backups": "no",
            "tag": "",
            "OSID": "159",
            "APPID": "0",
            "FIREWALLGROUPID": "0",
            "v2_id": "154714cb-3d9c-4463-9651-9ccb0d32e836",
            "id": "42164666",
            "image": "Custom Installed",
            "size": "201",
            "state": "active",
            "private_ips": "",
            "public_ips": "192.0.2.143",
        },
        "host2.example.com": {
            "SUBID": "35968667",
            "os": "CentOS SELinux 8 x64",
            "ram": "4096 MB",
            "disk": "Virtual 60 GB",
            "main_ip": "198.51.100.226",
            "vcpu_count": "2",
            "location": "Toronto",
            "DCID": "22",
            "default_password": "s%1,]d}>W-Pl2HwU",
            "date_created": "2020-04-20 10:20:00",
            "pending_charges": "4.47",
            "status": "active",
            "cost_per_month": "20.00",
            "current_bandwidth_gb": 0.045,
            "allowed_bandwidth_gb": "3000",
            "netmask_v4": "255.255.255.0",
            "gateway_v4": "198.51.100.1",
            "power_status": "running",
            "server_state": "ok",
            "VPSPLANID": "203",
            "v6_main_ip": "2001:db8:b001:beef:5400:02ff:feb2:bcb6",
            "v6_network_size": "64",
            "v6_network": "2001:db8:b001:beef::",
            "v6_networks": [
                {
                    "v6_main_ip": "2001:db8:b001:beef:5400:02ff:feb2:bcb6",
                    "v6_network_size": "64",
                    "v6_network": "2001:db8:b001:beef::",
                },
                {
                    "v6_main_ip": "2001:db8:b001:beef:5400:02ff:feb2:bcb6",
                    "v6_network_size": "64",
                    "v6_network": "2001:db8:b001:beef::",
                },
            ],
            "label": "host2.example.com",
            "internal_ip": "",
            "kvm_url": "https://my.vultr.com/subs/vps/novnc/api.php?data=Gohj4iepieBuw7eixa4dujaqu1veeheeGhaizuengaa6oo6eiphiezee2ohshieZ0phevieV-beemio8thai1eep2aihauje0Iez0chaeshae8oophushae3koe1QueebaiBoo4orooH2oongeeBeexaikaileu5iek6hahShiXiephoJee8Ohtha2uihahnoo6chahs-AB7-ephaaF8lu-phaephai9cheekaengashiw8ahc9voh1ia0tee9eiBeeK7Ohshaa",
            "auto_backups": "no",
            "tag": "",
            "OSID": "362",
            "APPID": "0",
            "FIREWALLGROUPID": "0",
            "v2_id": "bdb188ce-15d6-4964-a120-80886dea8108",
            "id": "35968667",
            "image": "CentOS SELinux 8 x64",
            "size": "203",
            "state": "active",
            "private_ips": "",
            "public_ips": "198.51.100.226",
        },
    }


def test_avail_locations_then_return_dict(locations):

    expected_result = locations

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_locations()

        assert actual_result == expected_result


def test_avail_sizes_then_return_dict(sizes):

    expected_result = sizes

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_sizes()

        assert actual_result == expected_result


def test_avail_images_then_return_dict(images):

    expected_result = images

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_images()

        assert actual_result == expected_result


def test_avail_scripts_then_return_dict(scripts):

    expected_result = scripts

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_scripts()

        assert actual_result == expected_result


def test_avail_acct_isos_then_return_dict(acct_isos):

    expected_result = acct_isos

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_acct_isos()

        assert actual_result == expected_result


def test_avail_public_isos_then_return_dict(public_isos):

    expected_result = public_isos

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_public_isos()

        assert actual_result == expected_result


def test_avail_keys_then_return_dict(keys):

    expected_result = keys

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_keys()

        assert actual_result == expected_result


def test_avail_firewall_groups_then_return_dict(firewall_groups):

    expected_result = firewall_groups

    with patch("salt.cloud.clouds.vultrpy._query", autospec=True) as query:

        query.return_value = expected_result

        actual_result = vultr.avail_firewall_groups()

        assert actual_result == expected_result


def test_show_keypair_then_return_dict(keys):

    expected_result = {
        "SSHKEYID": "6043ec83f126a",
        "date_created": "2021-03-06 20:56:35",
        "name": "ed25519 SSH Key",
        "ssh_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN1VVfN6mpiKlq5Es9mkdEtKQMblP3EkegEI3dHIIXcK ed25519 SSH Key",
        "v2_id": "121549dd-d43a-47fb-b87f-9a09afef8680",
    }

    with patch("salt.cloud.clouds.vultrpy.list_keypairs", autospec=True) as query:

        query.return_value = keys

        kwargs = {"keyname": "6043ec83f126a"}

        actual_result = vultr.show_keypair(kwargs)

        assert actual_result == expected_result


def test_show_keypair_no_keyname_then_error_message_should_be_logged(keys):

    kwargs = {}

    with patch("salt.cloud.clouds.vultrpy.log.error", autospec=True) as fake_error:

        vultr.show_keypair(kwargs)

        fake_error.assert_called_with("A keyname is required.")


def test_list_nodes_then_return_dict(nodes_full, nodes):

    expected_result = nodes

    with patch("salt.cloud.clouds.vultrpy.list_nodes_full", autospec=True) as query:

        query.return_value = nodes_full

        actual_result = vultr.list_nodes()

        assert actual_result == expected_result


def test_list_nodes_full_then_return_dict(nodes_full):

    expected_result = nodes_full

    with patch("salt.cloud.clouds.vultrpy.list_nodes_full", autospec=True) as query:

        query.return_value = nodes_full

        actual_result = vultr.list_nodes_full()

        assert actual_result == expected_result
