#
# Copyright (c) 2008--2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#
#
# shell script function library for rhn-bootstrap
#

import string
import os.path


_header = """\
#!/bin/bash
echo "{productName} Client bootstrap script v4.0"

# This file was autogenerated. Minor manual editing of this script (and
# possibly the client-config-overrides.txt file) may be necessary to complete
# the bootstrap setup. Once customized, the bootstrap script can be triggered
# in one of two ways (the first is preferred):
#
#   (1) centrally, from the {productName} via ssh (i.e., from the
#       {productName}):
#         cd {apachePubDirectory}/bootstrap/
#         cat bootstrap-<edited_name>.sh | ssh root@<client-hostname> /bin/bash
#
#   ...or...
#
#   (2) in a decentralized manner, executed on each client, via wget or curl:
#         wget -qO- https://<hostname>/pub/bootstrap/bootstrap-<edited_name>.sh | /bin/bash
#         ...or...
#         curl -Sks https://<hostname>/pub/bootstrap/bootstrap-<edited_name>.sh | /bin/bash

# SECURITY NOTE:
#   Use of these scripts via the two methods discussed is the most expedient
#   way to register machines to your {productName}. Since "wget" is used
#   throughout the script to download various files, a "Man-in-the-middle"
#   attack is theoretically possible.
#
#   The actual registration process is performed securely via SSL, so the risk
#   is minimized in a sense. This message merely serves as a warning.
#   Administrators need to appropriately weigh their concern against the
#   relative security of their internal network.

# PROVISIONING/KICKSTART NOTE:
#   If provisioning a client, ensure the proper CA SSL public certificate is
#   configured properly in the post section of your kickstart profiles (the
#   {productName} or hosted web user interface).

# UP2DATE/RHN_REGISTER VERSIONING NOTE:
#   This script will not work with very old versions of up2date and
#   rhn_register.


echo
echo
echo "MINOR MANUAL EDITING OF THIS FILE MAY BE REQUIRED!"
echo
echo "If this bootstrap script was created during the initial installation"
echo "of a {productName}, the ACTIVATION_KEYS, and ORG_GPG_KEY values will"
echo "probably *not* be set (see below). If this is the case, please do the"
echo "following:"
echo "  - copy this file to a name specific to its use."
echo "    (e.g., to bootstrap-SOME_NAME.sh - like bootstrap-web-servers.sh.)"
echo "  - on the website create an activation key or keys for the system(s) to"
echo "    be registered."
echo "  - edit the values of the VARIABLES below (in this script) as"
echo "    appropriate:"
echo "    - ACTIVATION_KEYS needs to reflect the activation key(s) value(s)"
echo "      from the website. XKEY or XKEY,YKEY"
echo "      Please note that if you are using this script to boostrap minions,"
echo "      only the FIRST activation key will be used. Multiple activation keys"
echo "      are not supported with salt"
echo "    - ORG_GPG_KEY needs to be set to the name(s) of the corporate public"
echo "      GPG key filename(s) (residing in {apachePubDirectory}) if appropriate. XKEY or XKEY,YKEY"
echo
echo "Verify that the script variable settings are correct:"
echo "    - CLIENT_OVERRIDES should be only set differently if a customized"
echo "      client-config-overrides-VER.txt file was created with a different"
echo "      name."
echo "    - ensure the value of HOSTNAME is correct."
echo "    - ensure the value of ORG_CA_CERT is correct."
echo
echo "Enable this script: comment (with #'s) this block (or, at least just"
echo "the exit below, if present)"
echo
{exit_call}

# can be edited, but probably correct (unless created during initial install):
# NOTE: ACTIVATION_KEYS *must* be used to bootstrap a client machine.
ACTIVATION_KEYS={activation_keys}
ORG_GPG_KEY={org_gpg_key}

# can be edited, but probably correct:
CLIENT_OVERRIDES={overrides}
HOSTNAME={hostname}

ORG_CA_CERT={orgCACert}
ORG_CA_CERT_IS_RPM_YN={isRpmYN}

USING_SSL={using_ssl}
USING_GPG={using_gpg}

REGISTER_THIS_BOX=1

ALLOW_CONFIG_ACTIONS={allow_config_actions}
ALLOW_REMOTE_COMMANDS={allow_remote_commands}

# this variable is only relevant for traditional clients and is ignored on salt minions
FULLY_UPDATE_THIS_BOX={up2dateYN}

# Set if you want to specify profilename for client systems.
# NOTE: Make sure it's set correctly if any external command is used.
#
# ex. PROFILENAME="foo.example.com"  # For specific client system
#     PROFILENAME=`hostname -s`      # Short hostname
#     PROFILENAME=`hostname -f`      # FQDN
PROFILENAME=""   # Empty by default to let it be set automatically.

# After registration, before updating the system (or at least the installer)
# disable all repos not provided by SUSE Manager.
DISABLE_LOCAL_REPOS=1

# Disable yasts automatic online update feature in case it is enabled
# on the client. Leaving automatic online update enabled, the client would
# continue to update himself independently from SUSE Manager requests.
DISABLE_YAST_AUTOMATIC_ONLINE_UPDATE=1

# SUSE Manager Specific settings:
#
# - Alternate location of the client tool repos providing the zypp-plugin-spacewalk
# and packges required for registration. Unless they are already installed on the
# client this repo is expected to provide them for SLE-10/SLE-11 based clients:
#   ${{CLIENT_REPOS_ROOT}}/sle/VERSION/PATCHLEVEL
# If empty, the SUSE Manager repositories provided at https://${{HOSTNAME}}/pub/repositories
# are used.
CLIENT_REPOS_ROOT=

#
# -----------------------------------------------------------------------------
# DO NOT EDIT BEYOND THIS POINT -----------------------------------------------
# -----------------------------------------------------------------------------
#

#
# do not try to register a SUSE Manager server at itself
#
MYNAME=`hostname -f`
LCMYNAME=`echo $MYNAME | tr '[:upper:]' '[:lower:]'`
LCHOSTNAME=`echo $HOSTNAME | tr '[:upper:]' '[:lower:]'`

if [ $LCMYNAME == $LCHOSTNAME ]; then
    echo "Name of client and of SUSE Manager server are the same."
    echo "Do not try to register a SUSE Manager server at itself!"
    echo "Aborting."
    exit 1
fi

# an idea from Erich Morisse (of Red Hat).
# use either wget *or* curl
# Also check to see if the version on the
# machine supports the insecure mode and format
# command accordingly.

if [ -x /usr/bin/wget ] ; then
    output=`LANG=en_US /usr/bin/wget --no-check-certificate 2>&1`
    error=`echo $output | grep "unrecognized option"`
    if [ -z "$error" ] ; then
        FETCH="/usr/bin/wget -nv -r -nd --no-check-certificate"
    else
        FETCH="/usr/bin/wget -nv -r -nd"
    fi
elif [ -x /usr/bin/curl ] ; then
    output=`LANG=en_US /usr/bin/curl -k 2>&1`
    error=`echo $output | grep "is unknown"`
    if [ -z "$error" ] ; then
        FETCH="/usr/bin/curl -ksSOf"
    else
        FETCH="/usr/bin/curl -sSOf"
    fi
else
    echo "To be able to download files, please install either 'wget' or 'curl'"
    exit 1
fi

HTTP_PUB_DIRECTORY=http://${{HOSTNAME}}/{pubname}
HTTPS_PUB_DIRECTORY=https://${{HOSTNAME}}/{pubname}
if [ $USING_SSL -eq 0 ] ; then
    HTTPS_PUB_DIRECTORY=${{HTTP_PUB_DIRECTORY}}
fi

INSTALLER=up2date
if [ -x /usr/bin/zypper ] ; then
    INSTALLER=zypper
elif [ -x /usr/bin/yum ] ; then
    INSTALLER=yum
fi

if [ ! -w . ] ; then
    echo ""
    echo "*** ERROR: $(pwd):"
    echo "    No permission to write to the current directory."
    echo "    Please execute this script in a directory where downloaded files can be stored."
    echo ""
    exit 1
fi
"""


def getHeader(productName, options, orgCACert, isRpmYN, pubname, apachePubDirectory):
    # 11/22/16 options.gpg_key is now a comma-separated list of path.
    # Removing paths from options.gpg_key
    org_gpg_key = ",".join([os.path.basename(gpg_key) for gpg_key in options.gpg_key.split(",")])
    exit_call = " " if options.activation_keys or options.salt else "exit 1"

    return _header.format(productName=productName,
                          apachePubDirectory=apachePubDirectory,
                          exit_call=exit_call,
                          activation_keys=options.activation_keys,
                          org_gpg_key=org_gpg_key,
                          overrides=options.overrides,
                          hostname=options.hostname,
                          orgCACert=orgCACert,
                          isRpmYN=isRpmYN,
                          using_ssl=0 if bool(options.no_ssl) else 1,
                          using_gpg=0 if bool(options.no_gpg) else 1,
                          allow_config_actions=options.allow_config_actions,
                          allow_remote_commands=options.allow_remote_commands,
                          up2dateYN=options.up2date,
                          pubname=pubname)

def getRegistrationStackSh(saltEnabled):
    """
    Determines which packages and repositories needs to be
    installed in order to register this system against SUMa server.
    """
    PKG_NAME = saltEnabled and ['salt', 'salt-minion'] or ['spacewalk-check', 'spacewalk-client-setup',
                                                           'spacewalk-client-tools', 'zypp-plugin-spacewalk']
    PKG_NAME_YUM = saltEnabled and ['salt', 'salt-minion'] or ['spacewalk-check', 'spacewalk-client-setup',
                                                               'spacewalk-client-tools', 'yum-rhn-plugin']

    PKG_NAME_UPDATE = list(PKG_NAME)
    PKG_NAME_UPDATE.extend(['zypper', 'openssl'])

    PKG_NAME_UPDATE_YUM = list(PKG_NAME_YUM)
    PKG_NAME_UPDATE_YUM.extend(saltEnabled and ['yum', 'openssl'] or ['yum-rhn-plugin', 'yum', 'openssl'])

    return """\
echo
echo "CLEANING UP OLD SUSE MANAGER REPOSITORIES"
echo "-------------------------------------------------"

function clean_up_old_trad_repos() {{
  local trad_client_repo_prefix="spacewalk:"
  if [ -f /usr/bin/realpath ]; then
    GET_PATH="/usr/bin/realpath"
  else
    GET_PATH="/usr/bin/readlink -f --"
  fi

  for file in $1/$trad_client_repo_prefix*.repo; do
    if [ -f "$file" ] ; then
      echo "Removing $($GET_PATH "$file")"
      rm -f $($GET_PATH "$file")
    fi
  done
}}

function clean_up_old_salt_repos() {{
  local salt_minion_channels_file="susemanager:channels.repo"

  if [ -f "$1/$salt_minion_channels_file" ] ; then
    echo "Removing $1/$salt_minion_channels_file"
    rm -f "$1/$salt_minion_channels_file"
  fi
}}

function clean_up_old_repos() {{
  local suse_os_repos_path="/etc/zypp/repos.d"
  local redhat_os_repos_path="/etc/yum.repos.d"

  clean_up_old_salt_repos $suse_os_repos_path
  clean_up_old_salt_repos $redhat_os_repos_path

  clean_up_old_trad_repos $suse_os_repos_path
  clean_up_old_trad_repos $redhat_os_repos_path
}}

clean_up_old_repos
echo
echo "CHECKING THE REGISTRATION STACK"
echo "-------------------------------------------------"

function test_repo_exists() {{
  local repourl="$CLIENT_REPO_URL"

  $FETCH $repourl/repodata/repomd.xml
  if [ ! -f "repomd.xml" ] ; then
    echo "Bootstrap repo '$repourl' does not exist."
    repourl=""
    CLIENT_REPO_URL=""
  fi
  rm -f repomd.xml
}}

function get_rhnlib_pkgs() {{
  # Gets all installed rhnlib packages for update
  RHNLIB_PKG=""
  if rpm -q python3-rhnlib > /dev/null; then
    RHNLIB_PKG+="python3-rhnlib "
  fi
  if rpm -q python2-rhnlib > /dev/null; then
    RHNLIB_PKG+="python2-rhnlib "
  fi
  if rpm -q rhnlib > /dev/null; then
    RHNLIB_PKG+="rhnlib "
  fi
}}

function setup_bootstrap_repo() {{
  local repopath="$CLIENT_REPO_FILE"
  local reponame="$CLIENT_REPO_NAME"
  local repourl="$CLIENT_REPO_URL"

  test_repo_exists

  if [ -n "$CLIENT_REPO_URL" ]; then
    echo " adding client software repository at $repourl"
    cat <<EOF >"$repopath"
[$reponame]
name=$reponame
baseurl=$repourl
enabled=1
autorefresh=1
keeppackages=0
gpgcheck=0
EOF
  fi
}}

function remove_bootstrap_repo() {{
  local repopath="$CLIENT_REPO_FILE"

  rm -f $repopath
}}

if [ "$INSTALLER" == yum ]; then
    function getY_CLIENT_CODE_BASE() {{
        local BASE=""
        local VERSION=""
        if [ -f /etc/centos-release ]; then
            grep -v '^#' /etc/centos-release | grep -q '\(CentOS\)' && BASE="centos"
            VERSION=`grep -v '^#' /etc/centos-release | grep -Po '(?<=release )\d+'`
        elif [ -f /etc/redhat-release ]; then
            grep -v '^#' /etc/redhat-release | grep -q '\(Red Hat\)' && BASE="res"
            VERSION=`grep -v '^#' /etc/redhat-release | grep -Po '(?<=release )\d+'`
        fi
        Y_CLIENT_CODE_BASE="${{BASE:-unknown}}"
        Y_CLIENT_CODE_VERSION="${{VERSION:-unknown}}"
    }}

    function getY_MISSING() {{
        local NEEDED="{PKG_NAME_YUM}"
        Y_MISSING=""
        for P in $NEEDED; do
            rpm -q "$P" || Y_MISSING="$Y_MISSING $P"
        done
    }}

    echo "* check for necessary packages being installed..."
    getY_CLIENT_CODE_BASE
    echo "* client codebase is ${{Y_CLIENT_CODE_BASE}}-${{Y_CLIENT_CODE_VERSION}}"
    getY_MISSING

    CLIENT_REPOS_ROOT="${{CLIENT_REPOS_ROOT:-https://${{HOSTNAME}}/pub/repositories}}"
    CLIENT_REPO_URL="${{CLIENT_REPOS_ROOT}}/${{Y_CLIENT_CODE_BASE}}/${{Y_CLIENT_CODE_VERSION}}/bootstrap"
    CLIENT_REPO_NAME="susemanager:bootstrap"
    CLIENT_REPO_FILE="/etc/yum.repos.d/$CLIENT_REPO_NAME.repo"

    setup_bootstrap_repo

    if [ -z "$Y_MISSING" ]; then
        echo "  no packages missing."
    else
        echo "* going to install missing packages..."

        yum -y install $Y_MISSING

        for P in $Y_MISSING; do
            rpm -q "$P" || {{
            echo "ERROR: Failed to install all missing packages."
            exit 1
        }}
        done
    fi
    # try update main packages for registration from any repo which is available
    get_rhnlib_pkgs
    yum -y upgrade {PKG_NAME_UPDATE_YUM} $RHNLIB_PKG ||:
fi
if [ "$INSTALLER" == zypper ]; then
  function getZ_CLIENT_CODE_BASE() {{
    local BASE=""
    local VERSION=""
    local PATCHLEVEL=""
    if [ -r /etc/SuSE-release ]; then
      grep -q 'Enterprise' /etc/SuSE-release && BASE='sle'
      eval $(grep '^\(VERSION\|PATCHLEVEL\)' /etc/SuSE-release | tr -d '[:blank:]')
    elif [ -r /etc/os-release ]; then
      grep -q 'Enterprise' /etc/os-release && BASE='sle'
      if [ "$BASE" != "sle" ]; then
         grep -q 'openSUSE' /etc/os-release && BASE='opensuse'
      fi
      VERSION="$(grep '^\(VERSION_ID\)' /etc/os-release | sed -n 's/.*"\([[:digit:]]\+\).*/\\1/p')"
      PATCHLEVEL="$(grep '^\(VERSION_ID\)' /etc/os-release | sed -n 's/.*\.\([[:digit:]]*\).*/\\1/p')"
    fi
    Z_CLIENT_CODE_BASE="${{BASE:-unknown}}"
    Z_CLIENT_CODE_VERSION="${{VERSION:-unknown}}"
    Z_CLIENT_CODE_PATCHLEVEL="${{PATCHLEVEL:-0}}"
  }}

  function getZ_MISSING() {{
    local NEEDED="{PKG_NAME}"
    if [ "$Z_CLIENT_CODE_BASE" == "sle" -a "$Z_CLIENT_CODE_VERSION" == "10" ]; then
      # (bnc#789373) Code 10 product migration requires 'xsltproc' being installed
      which 'xsltproc' || NEEDED="$NEEDED libxslt"
    fi
    Z_MISSING=""
    for P in $NEEDED; do
      rpm -q "$P" || Z_MISSING="$Z_MISSING $P"
    done
  }}

  function getZ_ZMD_TODEL() {{
    local ZMD_STACK="zmd rug libzypp-zmd-backend yast2-registration zen-updater zmd-inventory suseRegister-jeos"
    if rpm -q suseRegister --qf '%{{VERSION}}' | grep -q '^\(0\.\|1\.[0-3]\)\(\..*\)\?$'; then
      # we need the new suseRegister >= 1.4, so wipe an old one too
      ZMD_STACK="$ZMD_STACK suseRegister suseRegisterInfo spacewalk-client-tools"
    fi
    Z_ZMD_TODEL=""
    for P in $ZMD_STACK; do
      rpm -q "$P" && Z_ZMD_TODEL="$Z_ZMD_TODEL $P"
    done
  }}

  echo "* check for necessary packages being installed..."
  # client codebase determines repo url to use and whether additional
  # preparations are needed before installing the missing packages.
  getZ_CLIENT_CODE_BASE
  echo "* client codebase is ${{Z_CLIENT_CODE_BASE}}-${{Z_CLIENT_CODE_VERSION}}-sp${{Z_CLIENT_CODE_PATCHLEVEL}}"

  getZ_MISSING

  CLIENT_REPOS_ROOT="${{CLIENT_REPOS_ROOT:-${{HTTPS_PUB_DIRECTORY}}/repositories}}"
  CLIENT_REPO_URL="${{CLIENT_REPOS_ROOT}}/${{Z_CLIENT_CODE_BASE}}/${{Z_CLIENT_CODE_VERSION}}/${{Z_CLIENT_CODE_PATCHLEVEL}}/bootstrap"
  CLIENT_REPO_NAME="susemanager:bootstrap"
  CLIENT_REPO_FILE="/etc/zypp/repos.d/$CLIENT_REPO_NAME.repo"

  test_repo_exists

  if [ -z "$Z_MISSING" ]; then
    echo "  no packages missing."
    setup_bootstrap_repo
  else
    echo "* going to install missing packages..."

    # code10 requires removal of the ZMD stack first
    if [ "$Z_CLIENT_CODE_BASE" == "sle" ]; then
      if [ "$Z_CLIENT_CODE_VERSION" = "10" ]; then
	echo "* check whether to remove the ZMD stack first..."
	getZ_ZMD_TODEL
	if [ -z "$Z_ZMD_TODEL" ]; then
	  echo "  ZMD stack is not installed. No need to remove it."
	else
	  echo "  Disable and remove the ZMD stack..."
	  # stop any running zmd
	  if [ -x /usr/sbin/rczmd ]; then
	    /usr/sbin/rczmd stop
	  fi
	  rpm -e --nodeps $Z_ZMD_TODEL || {{
	    echo "ERROR: Failed remove the ZMD stack."
	    exit 1
	  }}
	fi
      fi
    fi

    # way to add the client software repository depends on the zypp version actually
    # installed (original code 10 via 'zypper sa', or code 11 like via .repo files)
    #
    # Note: We try to install the missing packages even if adding the repo fails.
    # Might be some other system repo provides them instead.
    if rpm -q zypper --qf '%{{VERSION}}' | grep -q '^0\(\..*\)\?$'; then

      # code10 zypper has no --gpg-auto-import-keys and no reliable return codes.
      if [ -n "$CLIENT_REPO_URL" ]; then
        echo "  adding client software repository at $CLIENT_REPO_URL"
        zypper --non-interactive --no-gpg-checks sd $CLIENT_REPO_NAME
        zypper --non-interactive --no-gpg-checks sa $CLIENT_REPO_URL $CLIENT_REPO_NAME
        zypper --non-interactive --no-gpg-checks refresh "$CLIENT_REPO_NAME"
      fi
      zypper --non-interactive --no-gpg-checks in $Z_MISSING
      for P in $Z_MISSING; do
	rpm -q --whatprovides "$P" || {{
	  echo "ERROR: Failed to install all missing packages."
	  exit 1
	}}
      done
      setup_bootstrap_repo
    else

      setup_bootstrap_repo

      zypper --non-interactive --gpg-auto-import-keys refresh "$CLIENT_REPO_NAME"
      # install missing packages
      zypper --non-interactive in $Z_MISSING
      for P in $Z_MISSING; do
	rpm -q --whatprovides "$P" || {{
	  echo "ERROR: Failed to install all missing packages."
	  exit 1
	}}
      done

    fi
  fi

  # on code10 we need to convert metadata of installed products
  if [ "$Z_CLIENT_CODE_BASE" == "sle" ]; then
    if [ "$Z_CLIENT_CODE_VERSION" = "10" ]; then
      test -e "/usr/share/zypp/migrate/10-11.migrate.products.sh" && {{
	echo "* check whether we have to to migrate metadata..."
	sh /usr/share/zypp/migrate/10-11.migrate.products.sh || {{
	  echo "ERROR: Failed to migrate product metadata."
	  exit 1
	}}
      }}
    fi
  fi

  get_rhnlib_pkgs
  # try update main packages for registration from any repo which is available
  zypper --non-interactive up {PKG_NAME_UPDATE} $RHNLIB_PKG ||:
fi

remove_bootstrap_repo

""".format(PKG_NAME=' '.join(PKG_NAME), PKG_NAME_YUM=' '.join(PKG_NAME_YUM),
           PKG_NAME_UPDATE=' '.join(PKG_NAME_UPDATE),
           PKG_NAME_UPDATE_YUM=' '.join(PKG_NAME_UPDATE_YUM))

def getConfigFilesSh():
    return """\
echo
echo "UPDATING RHN_REGISTER/UP2DATE CONFIGURATION FILES"
echo "-------------------------------------------------"
echo "* downloading necessary files"
echo "  client_config_update.py..."
rm -f client_config_update.py
$FETCH ${HTTPS_PUB_DIRECTORY}/bootstrap/client_config_update.py
echo "  ${CLIENT_OVERRIDES}..."
rm -f ${CLIENT_OVERRIDES}
$FETCH ${HTTPS_PUB_DIRECTORY}/bootstrap/${CLIENT_OVERRIDES}

if [ ! -f "client_config_update.py" ] ; then
    echo "ERROR: client_config_update.py was not downloaded"
    exit 1
fi
if [ ! -f "${CLIENT_OVERRIDES}" ] ; then
    echo "ERROR: ${CLIENT_OVERRIDES} was not downloaded"
    exit 1
fi

"""

def getUp2dateScriptsSh():
    return """\
echo "* running the update scripts"
if [ -x "/usr/bin/python" ] ; then
    PYTHON=/usr/bin/python
elif [ -x /usr/bin/python3 ]; then
    PYTHON=/usr/bin/python3
else
   echo "No python found"
   exit 1
fi
if [ -f "/etc/sysconfig/rhn/rhn_register" ] ; then
    echo "  . rhn_register config file"
    $PYTHON -u client_config_update.py /etc/sysconfig/rhn/rhn_register ${CLIENT_OVERRIDES}
fi
if [ -f "/etc/sysconfig/rhn/up2date" ] ; then
  echo "  . up2date config file"
  $PYTHON -u client_config_update.py /etc/sysconfig/rhn/up2date ${CLIENT_OVERRIDES}
fi

"""


def getGPGKeyImportSh():
    return """\
echo
echo "PREPARE GPG KEYS AND CORPORATE PUBLIC CA CERT"
echo "-------------------------------------------------"
if [ ! -z "$ORG_GPG_KEY" ] ; then
    echo
    echo "* importing organizational GPG keys"
    for GPG_KEY in $(echo "$ORG_GPG_KEY" | tr "," " "); do
        rm -f ${GPG_KEY}
        $FETCH ${HTTPS_PUB_DIRECTORY}/${GPG_KEY}
        # get the major version of up2date
        # this will also work for RHEL 5 and systems where no up2date is installed
        res=$(LC_ALL=C rpm -q --queryformat '%{version}' up2date | sed -e 's/\..*//g')
        if [ "x$res" == "x2" ] ; then
            gpg $(up2date --gpg-flags) --import $GPG_KEY
        else
            rpm --import $GPG_KEY
        fi
    done
else
    echo "* no organizational GPG keys to import"
fi

"""


def getCorpCACertSh():
    return """\
echo
if [ $USING_SSL -eq 1 ] ; then

    CERT_DIR=/usr/share/rhn
    TRUST_DIR=/etc/pki/ca-trust/source/anchors
    UPDATE_TRUST_CMD="/usr/bin/update-ca-trust extract"

    if [  $ORG_CA_CERT_IS_RPM_YN -eq 1 ] ; then
      # get name from config
      CERT_FILE=$(basename $(sed -n 's/^sslCACert *= *//p' "${CLIENT_OVERRIDES}"))
    else
      CERT_FILE=${ORG_CA_CERT}
    fi

    function updateCertificates() {
        if [ -d /etc/pki/ca-trust/source/anchors ]; then
            TRUST_DIR=/etc/pki/ca-trust/source/anchors
        elif [ -d /etc/pki/trust/anchors/ -a -x /usr/sbin/update-ca-certificates ]; then
            # SLE 12
            TRUST_DIR=/etc/pki/trust/anchors
            UPDATE_TRUST_CMD="/usr/sbin/update-ca-certificates"
        elif [ -d /etc/ssl/certs -a -x /usr/bin/c_rehash ]; then
            # SLE 11
            TRUST_DIR=/etc/ssl/certs
            UPDATE_TRUST_CMD="/usr/bin/c_rehash"
            rm -f $TRUST_DIR/RHN-ORG-TRUSTED-SSL-CERT.pem
            rm -f $TRUST_DIR/RHN-ORG-TRUSTED-SSL-CERT-*.pem
            if [ -f $CERT_DIR/$CERT_FILE ]; then
                ln -sf $CERT_DIR/$CERT_FILE $TRUST_DIR/RHN-ORG-TRUSTED-SSL-CERT.pem
                if [ $(grep -- "-----BEGIN CERTIFICATE-----" $CERT_DIR/$CERT_FILE | wc -l) -gt 1 ]; then
                    csplit -b "%02d.pem" -f $TRUST_DIR/RHN-ORG-TRUSTED-SSL-CERT- $CERT_DIR/$CERT_FILE '/-----BEGIN CERTIFICATE-----/' '{*}'
                fi
            fi
            $UPDATE_TRUST_CMD >/dev/null
            return
        fi

        if [ ! -d $TRUST_DIR ]; then
            return
        fi

        if [ -f $CERT_DIR/$CERT_FILE ]; then
            ln -sf $CERT_DIR/$CERT_FILE $TRUST_DIR
        else
            rm -f $TRUST_DIR/$CERT_FILE
        fi

        $UPDATE_TRUST_CMD
    }

    echo "* attempting to install corporate public CA cert"

    ### Check for Dynamic CA-Trust Updates - applies to RedHat and SLE-ES systems ###
    if [ -x /usr/bin/update-ca-trust ] ; then
        if [ "$(/usr/bin/update-ca-trust check | grep 'PEM/JAVA Status: DISABLED')" != "" ]; then
            echo "ERROR: Dynamic CA-Trust > Updates are disabled. Enable Dynamic CA-Trust Updates with '/usr/bin/update-ca-trust force-enable'"
            echo "Finally, restart the onboarding sequence."
            exit 1
        fi
    fi

    test -d ${CERT_DIR} || mkdir -p ${CERT_DIR}
    rm -f ${ORG_CA_CERT}
    $FETCH ${HTTPS_PUB_DIRECTORY}/${ORG_CA_CERT}

    if [ $ORG_CA_CERT_IS_RPM_YN -eq 1 ] ; then
        rpm -Uvh --force --replacefiles --replacepkgs ${ORG_CA_CERT}
        rm -f ${ORG_CA_CERT}
    else
        mv ${ORG_CA_CERT} ${CERT_DIR}
    fi

    if [  $ORG_CA_CERT_IS_RPM_YN -eq 0 ] ; then
        # symlink & update certificates is already done in rpm post-install script
        # no need to be done again if we have installed rpm
        echo "* update certificates"
        updateCertificates
    fi
else
    echo "* configured not to use SSL: don't install corporate public CA cert"
fi

"""


#5/16/05 wregglej 159437 - changed script to use rhn-actions-control
def getAllowConfigManagement():
    return """\
if [ $ALLOW_CONFIG_ACTIONS -eq 1 ] ; then
    echo
    echo "* setting permissions to allow configuration management"
    echo "  NOTE: use an activation key to subscribe to the tools"
    if [ "$INSTALLER" == zypper ] ; then
        echo "        channel and zypper install/update rhncfg-actions"
    elif [ "$INSTALLER" == yum ] ; then
        echo "        channel and yum upgrade rhncfg-actions"
    else
        echo "        channel and up2date rhncfg-actions"
    fi
    if [ -x "/usr/bin/rhn-actions-control" ] ; then
        rhn-actions-control --enable-all
        rhn-actions-control --disable-run
    else
        echo "Error setting permissions for configuration management."
        echo "    Please ensure that the activation key subscribes the"
        if [ "$INSTALLER" == zypper ] ; then
            echo "    system to the tools channel and zypper install/update rhncfg-actions."
        elif [ "$INSTALLER" == yum ] ; then
            echo "    system to the tools channel and yum updates rhncfg-actions."
        else
            echo "    system to the tools channel and up2dates rhncfg-actions."
        fi
        exit
    fi
fi

"""


#5/16/05 wregglej 158437 - changed script to use rhn-actions-control
def getAllowRemoteCommands():
    return """\
if [ $ALLOW_REMOTE_COMMANDS -eq 1 ] ; then
    echo
    echo "* setting permissions to allow remote commands"
    echo "  NOTE: use an activation key to subscribe to the tools"
    if [ "$INSTALLER" == zypper ] ; then
        echo "        channel and zypper update rhncfg-actions"
    elif [ "$INSTALLER" == yum ] ; then
        echo "        channel and yum upgrade rhncfg-actions"
    else
        echo "        channel and up2date rhncfg-actions"
    fi
    if [ -x "/usr/bin/rhn-actions-control" ] ; then
        rhn-actions-control --enable-run
    else
        echo "Error setting permissions for remote commands."
        echo "    Please ensure that the activation key subscribes the"
        if [ "$INSTALLER" == zypper ] ; then
            echo "    system to the tools channel and zypper updates rhncfg-actions."
        elif [ "$INSTALLER" == yum ] ; then
            echo "    system to the tools channel and yum updates rhncfg-actions."
        else
            echo "    system to the tools channel and up2dates rhncfg-actions."
        fi
        exit
    fi
fi

"""


def getRegistrationSh(productName):
    return """\
echo
echo "REGISTRATION"
echo "------------"
# Should have created an activation key or keys on the {productName}'s
# website and edited the value of ACTIVATION_KEYS above.
#
# If you require use of several different activation keys, copy this file and
# change the string as needed.
#
if [ -z "$ACTIVATION_KEYS" ] ; then
    echo "*** ERROR: in order to bootstrap {productName} clients, an activation key or keys"
    echo "           must be created in the {productName} web user interface, and the"
    echo "           corresponding key or keys string (XKEY,YKEY,...) must be mapped to"
    echo "           the ACTIVATION_KEYS variable of this script."
    exit 1
fi

if [ $REGISTER_THIS_BOX -eq 1 ] ; then
    echo "* registering"
    files=""
    directories=""
    if [ $ALLOW_CONFIG_ACTIONS -eq 1 ] ; then
        for i in "/etc/sysconfig/rhn/allowed-actions /etc/sysconfig/rhn/allowed-actions/configfiles"; do
            [ -d "$i" ] || (mkdir -p $i && directories="$i $directories")
        done
        [ -f /etc/sysconfig/rhn/allowed-actions/configfiles/all ] || files="$files /etc/sysconfig/rhn/allowed-actions/configfiles/all"
        [ -n "$files" ] && touch  $files
    fi
    if [ -z "$PROFILENAME" ] ; then
        profilename_opt=""
    else
        profilename_opt="--profilename=$PROFILENAME"
    fi
    /usr/sbin/rhnreg_ks --force --activationkey "$ACTIVATION_KEYS" $profilename_opt
    RET="$?"
    [ -n "$files" ] && rm -f $files
    [ -n "$directories" ] && rmdir $directories
    if [ $RET -eq 0 ]; then
      echo
      echo "*** this system should now be registered, please verify ***"
      echo
    else
      echo
      echo "*** Error: Registering the system failed."
      echo
      exit 1
    fi
else
    echo "* explicitly not registering"
fi

""".format(productName=productName)

def getRegistrationSaltSh(productName):
    return """\
echo
echo "REGISTRATION"
echo "------------"
# Should have created an activation key or keys on the {productName}'s
# website and edited the value of ACTIVATION_KEYS above.
#
# If you require use of several different activation keys, copy this file and
# change the string as needed.
#

MINION_ID_FILE="/etc/salt/minion_id"
SUSEMANAGER_MASTER_FILE="/etc/salt/minion.d/susemanager.conf"

if [ $REGISTER_THIS_BOX -eq 1 ] ; then
    echo "* registering"

    echo "$MYNAME" > "$MINION_ID_FILE"
    echo "master: $HOSTNAME" > "$SUSEMANAGER_MASTER_FILE"

    if [ -n "$ACTIVATION_KEYS" ] ; then
        cat <<EOF >>"$SUSEMANAGER_MASTER_FILE"
grains:
    susemanager:
        activation_key: "$(echo $ACTIVATION_KEYS | cut -d, -f1)"
EOF
    fi
fi

echo "* removing TLS certificate used for bootstrap"
echo "  (will be re-added via salt state)"

removeTLSCertificate

echo "* starting salt daemon and enabling it during boot"

if [ -f /usr/lib/systemd/system/salt-minion.service ] ; then
    systemctl enable salt-minion
    systemctl restart salt-minion
else
    /etc/init.d/salt-minion restart
    /sbin/chkconfig --add salt-minion
fi
echo "-bootstrap complete-"
""".format(productName=productName)


def removeTLSCertificate():
    """
    This method adds bash instructions to the bootstrap script to correctly
    remove TLS certificate used to install salt packages to bootstrap the
    minion.
    Since TLS certificates will be installed again with a Salt state during
    onboarding, this is required to avoid duplicates in TLS certificates.
    """

    return """\
function removeTLSCertificate() {
    CERT_DIR=/usr/share/rhn
    TRUST_DIR=/etc/pki/ca-trust/source/anchors
    UPDATE_TRUST_CMD="/usr/bin/update-ca-trust extract"

    if [ $ORG_CA_CERT_IS_RPM_YN -eq 1 ] ; then
        CERT_FILE=$(basename $(sed -n 's/^sslCACert *= *//p' "${CLIENT_OVERRIDES}"))
        rpm -e `basename ${ORG_CA_CERT} .rpm`
    else
        CERT_FILE=${ORG_CA_CERT}
        rm -f /usr/share/rhn/${ORG_CA_CERT}
    fi
    updateCertificates
}

    """


def getUp2dateTheBoxSh(productName, saltEnabled):
    if saltEnabled:
        PKG_NAME_ZYPPER = PKG_NAME_ZYPPER_SYNC = \
        PKG_NAME_YUM = PKG_NAME_YUM_SYNC = "salt salt-minion"
    else:
        PKG_NAME_ZYPPER = "zypp-plugin-spacewalk"
        PKG_NAME_YUM = "yum-rhn-plugin"
        PKG_NAME_ZYPPER_SYNC = PKG_NAME_ZYPPER + "; rhn-profile-sync"
        PKG_NAME_YUM_SYNC = PKG_NAME_YUM + "; rhn-profile-sync"

    return """\
echo
echo "OTHER ACTIONS"
echo "------------------------------------------------------"
SALT_ENABLED={saltEnabled}
if [ $DISABLE_YAST_AUTOMATIC_ONLINE_UPDATE -eq 1 ]; then
    YAOU_SYSCFGFILE="/etc/sysconfig/automatic_online_update"
    if [ -f "$YAOU_SYSCFGFILE" ]; then
      echo "* Disable YAST automatic online update."
      sed -i 's/^ *AOU_ENABLE_CRONJOB.*/AOU_ENABLE_CRONJOB="false"/' "$YAOU_SYSCFGFILE"
      for D in /etc/cron.*; do
	test -L $D/opensuse.org-online_update && rm $D/opensuse.org-online_update
      done
    fi
fi
if [ "$INSTALLER" == zypper ] ; then
  test -d /var/lib/suseRegister && touch /var/lib/suseRegister/neverRegisterOnBoot
fi
if [ $DISABLE_LOCAL_REPOS -eq 1 ] && [ $SALT_ENABLED -eq 0 ] ; then
    if [ "$INSTALLER" == zypper ] ; then
	echo "* Disable all repos not provided by SUSE Manager Server."
	zypper ms -d --all
	zypper ms -e --medium-type plugin
	zypper mr -d --all
	zypper mr -e --medium-type plugin
	zypper mr -e "$CLIENT_REPO_NAME"
    elif [ "$INSTALLER" == yum ] ; then
        echo "* Disable all repos not provided by SUSE Manager Server.";
	for F in /etc/yum.repos.d/*.repo; do
	  test -f "$F" || continue
	  # parse throught the file and make sure each repo section contains 'enabled=0'
	  awk '
	    BEGIN           {{ saw=0 }}
	    /^ *[[]/        {{ if ( saw==1 ) print "enabled=0"; else saw=1 }}
	    /^ *enabled *=/ {{ print "enabled=0"; saw=2; next }}
			    {{ print }}
	    END             {{ if ( saw==1 ) print "enabled=0" }}
	  ' "$F" > "$F.bootstrap.tmp" && mv "$F.bootstrap.tmp" "$F"
	  test -f  "$F.bootstrap.tmp" && {{
	    echo "*** Error: Failed to process '$F'; check manually if all repos inside are disabled."
	    rm "$F.bootstrap.tmp"
	  }}
	done
    fi
fi
if [ $FULLY_UPDATE_THIS_BOX -eq 1 ] ; then
    if [ "$INSTALLER" == zypper ] ; then
        echo "zypper --non-interactive up zypper {PKG_NAME_ZYPPER_SYNC}; zypper --non-interactive up (conditional)"
    elif [ "$INSTALLER" == yum ] ; then
        echo "yum -y upgrade yum {PKG_NAME_YUM_SYNC}; yum upgrade (conditional)"
    else
        echo "up2date up2date; up2date -p; up2date -uf (conditional)"
    fi
else
    if [ "$INSTALLER" == zypper ] ; then
        echo "zypper --non-interactive up zypper {PKG_NAME_ZYPPER_SYNC}"
    elif [ "$INSTALLER" == yum ] ; then
        echo "yum -y upgrade yum {PKG_NAME_YUM_SYNC}"
    else
        echo "up2date up2date; up2date -p"
    fi
fi
echo "but any post configuration action can be added here.  "
echo "------------------------------------------------------"
if [ $FULLY_UPDATE_THIS_BOX -eq 1 ] ; then
    echo "* completely updating the box"
else
    echo "* ensuring $INSTALLER itself is updated"
fi
if [ "$INSTALLER" == zypper ] ; then
    zypper lr -u
    if [ $SALT_ENABLED -eq 0 ] ; then
        zypper --non-interactive ref -s
    fi
    zypper --non-interactive up zypper {PKG_NAME_ZYPPER}
    if [ $SALT_ENABLED -eq 0 ] ; then
        if [ -x /usr/sbin/rhn-profile-sync ] ; then
            /usr/sbin/rhn-profile-sync
        else
            echo "Error updating system info in {productName}."
            echo "    Please ensure that rhn-profile-sync in installed and rerun it."
        fi
    fi
    if [ $FULLY_UPDATE_THIS_BOX -eq 1 ] ; then
        zypper --non-interactive up
    fi
elif [ "$INSTALLER" == yum ] ; then
    yum repolist
    /usr/bin/yum -y upgrade yum {PKG_NAME_YUM}
    if [ $SALT_ENABLED -eq 0 ] ; then
        if [ -x /usr/sbin/rhn-profile-sync ] ; then
            /usr/sbin/rhn-profile-sync
        else
            echo "Error updating system info in {productName}."
            echo "    Please ensure that rhn-profile-sync in installed and rerun it."
        fi
    fi
    if [ $FULLY_UPDATE_THIS_BOX -eq 1 ] ; then
        /usr/bin/yum -y upgrade
    fi
else
    /usr/sbin/up2date up2date
    /usr/sbin/up2date -p
    if [ $FULLY_UPDATE_THIS_BOX -eq 1 ] ; then
        /usr/sbin/up2date -uf
    fi
fi
echo "-bootstrap complete-"
""".format(saltEnabled=saltEnabled,
           PKG_NAME_ZYPPER_SYNC=PKG_NAME_ZYPPER_SYNC,
           PKG_NAME_YUM_SYNC=PKG_NAME_YUM_SYNC,
           PKG_NAME_ZYPPER=PKG_NAME_ZYPPER,
           PKG_NAME_YUM=PKG_NAME_YUM,
           productName=productName)
