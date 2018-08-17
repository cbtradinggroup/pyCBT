"""This module handles classes and functions for OANDA account configuration

The classes and functions here are meant for configuration purposes only
since they require user interaction through command line.

For interacting directly with the OANDA API, please use the oandapyV20
wrapper (https://github.com/hootnot/oanda-api-v20) upon which this module
is built.
"""

import sys, os, string

from collections import OrderedDict
from ruamel.yaml import YAML
import oandapyV20
from oandapyV20.endpoints.accounts import AccountList, AccountInstruments
from pyCBT import data_path


# TODO: use JSON for summary storage instead of YAML (more standard approach)
class Config(object):
    """Given a OANDA token, generate a config summary.

    Essentially this class provides a badge card to access one account
    associated with your token. This bagde card, called 'self.summary' can be
    stored in a file, loaded from a file or generated interactively by command
    line interaction.

    The attributes can come from three sources:
        - Default values stored in self.attr_defaults.
        - A pre-built config file compliant with the required format (see example
          below).
        - Keyword arguments (kwargs) provided on initialization of the class or
          latter on.

    There are three important set of variables to the final objective of this class
    (the 'self.summary'), namely: 'self.attr_defaults', the group of attributes
    'self.environment', 'self.timeout', 'self.token', 'self.username',
    'self.timezone', 'self.datetime_format', 'self.accounts' and 'self.account',
    and finally, the 'self.summary' attribute itself. Each is manipulated in stages
    under full control of the user, and ONLY when the method 'self.set_summary' is
    called, presumably (and necessarily) when all items in 'self.attr_defaults' are
    not 'None', 'self.summary' and the previous group of attributes are set to the
    values in the first.

    The 'self.attr_defaults' attribute holds the current defaults for the config
    object. However, on initialization, the 'self.attr_defaults' can be updated
    through the 'kwargs'. Later on, 'self.attr_defaults' can be (again) updated
    through the 'self.update_defaults' method using a different set of 'kwargs'.
    Please note that any of these sources may contain missing values. In fact,
    by default, 'self.attr_defaults' is not aware of 'username' nor 'account'.

    Finally, the 'self.summary' can be stored ('self.dump_to') in a file. To ensure
    format compliance and reachability of this file through this class instances, there
    are three helper methods: 'self.get_filename', to build a full path to the file,
    and 'self.dump_to'/'self.get_from' methods to store/load the 'self.summary' variable.

    Parameters
    ----------
    **kwargs : dictionary, optional
        keyword attributes that can be passed through command line. Valid keys
        are:

        * token: the access token given by OANDA.
        * environment: API url environment: 'practice' (default) or 'live'.
        * timeout: lifetime of the pending request in seconds (defaults to 1.0).
        * accounts: accounts registered for given a token.
        * account: currently used account.
        * username: the user holding the token.
        * timezone: timezone for series alignment (defaults to 'UTC').
        * datetime_format: format used for datetime strings: 'RFC3339' (default) or 'UNIX'.
    """

    def __init__(self, **kwargs):

        self.attr_names = [
            "token",
            "environment",
            "timeout",
            "accounts",
            "account",
            "username",
            "timezone",
            "datetime_format"
        ]
        self.attr_defaults = OrderedDict(zip(
            self.attr_names,
            [
                kwargs.pop("token", None),
                kwargs.pop("enviroment", "practice"),
                kwargs.pop("timeout", 1.0),
                kwargs.pop("accounts", None),
                kwargs.pop("account", None),
                kwargs.pop("username", None),
                kwargs.pop("timezone", "UTC"),
                kwargs.pop("datetime_format", "RFC3339")
            ]
        ))
        self.attr_helps = OrderedDict(zip(
            self.attr_names,
            [
                "API authorization token",
                "Server environment",
                "Timeout of the requests in seconds",
                "Accounts owned by user",
                "Currently active account",
                "Username of the account owner",
                "Timezone for series alignment",
                "Datetime format"
            ]
        ))
        self.attr_types = OrderedDict(zip(
            self.attr_names,
            [
                None,
                None,
                float,
                list,
                None,
                None,
                None,
                None
            ]
        ))
        self.attr_choices = OrderedDict(zip(
            self.attr_names,
            [
                None,
                ("practice", "live"),
                None,
                None,
                None,
                None,
                None,
                ("RFC3339", "UNIX")
            ]
        ))

        self.token = None
        self.environment = None
        self.timeout = None
        self.accounts = None
        self.account = None
        self.username = None
        self.timezone = None
        self.datetime_format = None

        self.summary = None

        self._filename_template = os.path.join(data_path, ".oanda-account{}.yml")
        self._filename = None

    def update_defaults(self, **kwargs):
        """Update default attribute values to given keyword arguments
        """
        self.attr_defaults.update(kwargs)
        return None

    # TODO: move this function to common package
    def ask_the_user(self, header, choices=None, question=None, default=None, dtype=None):
        """Ask the user to set the value for given attribute from several options

        Parameters
        ----------
        header: string
            Description of the choices.
        choices: list or tuple
            Choices to choose from.
        question: string
            Ask user to choose one of the options.
        default: any
            Default value for the attribute.
        dtype: type object, optional
            Data type to asign value given by the user.
        """
        # if not given choices, ask plain
        print
        if choices is None:
            if default is None:
            #   ask for value
                value = raw_input("{}: ".format(header))
            # else if default value present
            else:
            #   ask for value with default value
                value = raw_input("{} [{}]: ".format(header, default))
            #   parse value from user
                if value == "": value = str(default)
            # if not given data type
            if dtype is None:
            #   return plain string with value
                return value
            # else if given data type
            else:
            #   evaluate given string value
                value = eval(value)
            #   check if given value is the same type as given
                if not type(value) == dtype:
            #       raise error if type mismatch
                    raise TypeError("{} is not {} type".format(value, dtype))
            return value
        # else, ask choice
        else:
            if len(choices)==1: default = choices[0]
            # display list of choices
            print "{}:".format(header)
            for i, choice in enumerate(choices):
                print "[{}] {}".format(i+1, choice)
            # if not default choice present
            if default is None:
            #   ask for choice
                select = raw_input("{}?: ".format(question or "Your choice"))
            # else if default choice present
            else:
            #   define index of default choice
                i_default = choices.index(default) + 1
            #   ask for choice with default value
                select = raw_input("{}? [{}]: ".format(question or "Your choice", i_default))
            #   parse choice from user
                if select == "":
                    select = i_default - 1
                else:
                    select = int(select) - 1
            return choices[select]

    def ask_attributes(self, only_missing=False):
        for attr_name in self.attr_names:
            if only_missing and self.attr_defaults[attr_name] is not None: continue
            if attr_name == "accounts":
                # get accounts
                api = oandapyV20.API(
                    access_token=self.attr_defaults["token"],
                    environment=self.attr_defaults["environment"],
                    request_params={"timeout": self.attr_defaults["timeout"]}
                )
                # generate request to account list endpoint
                r = AccountList()
                api.request(r)
                # store list of account IDs
                self.attr_defaults[attr_name] = [account["id"] for account in r.response["accounts"]]
                self.attr_choices["account"] = self.attr_defaults[attr_name]
            else:
                self.attr_defaults[attr_name] = self.ask_the_user(
                    header=self.attr_helps[attr_name],
                    choices=self.attr_choices[attr_name],
                    question="Select the {}".format(attr_name),
                    default=self.attr_defaults[attr_name],
                    dtype=self.attr_types[attr_name]
                )
        return None

    def set_summary(self):
        """Set config attributes & summary in dictionary

        This method requires that all summary items are set. So it should be called
        only after calling ask_/set_account & ask_/set_attributes successfully.
        Otherwise a ValueError will be raised.
        """
        # set config attributes
        self.token = self.attr_defaults["token"]
        self.environment = self.attr_defaults["environment"]
        self.timeout = self.attr_defaults["timeout"]
        self.accounts = self.attr_defaults["accounts"]
        self.account = self.attr_defaults["account"]
        self.username = self.attr_defaults["username"]
        self.timezone = self.attr_defaults["timezone"]
        self.datetime_format = self.attr_defaults["datetime_format"]
        # define config summary dictionary
        _summary = [
            self.token,
            self.environment,
            self.timeout,
            self.accounts,
            self.account,
            self.username,
            self.timezone,
            self.datetime_format
        ]
        if None in _summary:
            missing = string.join(
                [self.attr_names[i] for i in xrange(len(_summary)) if _summary[i] is None], ", "
            )
            raise ValueError(
                "The following items from the summary are undefined: {}.".format(missing)
            )
        self.summary = OrderedDict(zip(self.attr_names, _summary))
        return None

    def get_filename(self, account=None):
        """Return config filename
        """
        if account is not None:
            self._filename = self._filename_template.format("-"+account)
        else:
            self._filename = self._filename_template.format("")
        return self._filename

    def dump_to(self, file):
        """Dump config attributes to file

        This method requires that 'summary' is already set.
        """
        if self.summary is None:
            raise ValueError("You must define 'summary' first.")
        # instantiate yaml object
        yaml = YAML()
        # dump config summary in config file
        yaml.dump(self.summary, file)
        return None

    def get_from(self, file=None):
        """Load config attributes from file
        """
        # instantiate yaml object
        yaml = YAML()
        # load config file
        summary = yaml.load((file if file is not None else open(self.get_filename(), "r")))
        # return file content in dictionary
        return summary

# TODO: take as input the config object (optional)
class Client(object):
    """Create an API client for OANDA crendentials given a account ID.

    Given a user account this class will summon an API client using the account
    configuration from a pre-built config file associated with that account. If
    the account is not given, the account configuration will be loaded from the
    default (pre-built) config file. The token is kept private all along. However,
    if the given account does not have a config file and the default is
    successfully loaded (or_default=True), the accounts will be compared as a
    measure of security.
    """

    def __init__(self, account=None, try_default=True):
        # initialize config object
        config = Config()
        # if not account given, try default config file or die
        if account is None:
            try:
                conf_filename = config.get_filename()
                account_summary = config.get_from(file=open(conf_filename, "r"))
            except IOError:
                raise IOError(
                    "The default config file does not exist.\nPlease run cbt-config.py."
                )
        # else if account given and not try default, try account config file or die
        elif account is not None and not try_default:
            try:
                conf_filename = config.get_filename(account)
                account_summary = config.get_from(file=open(conf_filename, "r"))
            except IOError:
                raise IOError(
                    "The config file '{}' does not exist.\nPlease run cbt-config.py.".format(conf_filename)
                )
        # else, try both
        else:
            try:
                conf_filename = config.get_filename(account)
                account_summary = config.get_from(file=open(conf_filename, "r"))
            except IOError:
                pass
            try:
                conf_filename = config.get_filename()
                account_summary = config.get_from(file=open(conf_filename, "r"))
            except IOError:
                raise IOError(
                    "No config file associated with the given account was found.\nPlease run cbt-config.py."
                )

        if account is not None:
            if not account in account_summary.get("accounts"):
                raise ValueError(
                    "The config file '{}' is corrupt.\nPlease run cbt-config.py.".format(conf_filename)
                )

        # initialize API client
        # TODO: the token is still visible from self.api, use object properties to hide this information
        self.api = oandapyV20.API(
            access_token=account_summary.pop("token"),
            environment=account_summary.pop("environment"),
            request_params={"timeout": account_summary.pop("timeout")}
        )
        # store the rest of the account attributes
        self.account_summary = account_summary

    def reset_client(self, **kwargs):
        self.api.close()
        self.api = oandapyV20.API(
            access_token=kwargs.pop("token"),
            environment=kwargs.pop("environment"),
            request_params={"timeout": kwargs.pop("timeout")}
        )
        return None

class Instruments(object):
    """Builds a list of tradeable instruments from the OANDA account
    """
    def __init__(self, client):
        r = AccountInstruments(accountID=client.account_summary.get("account"))
        client.api.request(r)
        response = r.response.get("instruments")
        self.table = {inst["name"]: {"name": inst["displayName"], "type": inst["type"]} for inst in response}
