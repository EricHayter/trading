from configparser import ConfigParser
from datetime import datetime, timedelta
from enum import Enum

"""rate-limiter

This module is meant to facilitate rate limiting with a simple
interface. A user will create a limits configuration file which 
will store the maximum amount of requests to be made in certain units
of time, e.g. 800 requests in a day and 8 per minute.
"""

class Units(Enum):
    """Enumeration class to represent different units of
    time 

    The value of each of the elements map to their
    respective index found in a datetime.timetuple() object to 
    simplify iteration.
    """

    YEAR = 0
    MONTH = 1
    DAY = 2
    HOUR = 3
    MINUTE = 4
    SECOND = 5

class RateLimiter:
    """A class to manage rate limiting applications

    The class can be configured to limit the amount of usage per 
    specific units of time that are found in the Units enumeration
    class.

    Attributes
    ----------
    cfg_file : str
        file location for configuration (default 'limits.cfg')
    config : configparser.ConfigParser 
        config parser object for writting and storing rate limits and
        usage
    usage : dict
        stores the amount of requests made during each unit of time
    latest_time : datetime.datetime
        datetime object representing the last time a request was made


    Methods
    -------
    update_limits(**kwargs)
        updates the amount of requests per unit of time provided by
        keyword arguments and then writes the new limits to the config
        file
    write_usage()
        saves usage dictionary to configuration file
    cooldown(Units)
        gives the number of seconds until another request can be made
    request(func, *args, **kwargs)
        calls the function func and increments usage 
    """

    def __init__(self, cfg_file=None):
        '''
        Parameters
        ---------
        cfg_file : str
            the location of the config file
        '''

        self.usage = dict()
        if cfg_file == None:
            self.cfg_file = 'limits.ini'
            self.config = ConfigParser()
            self.config['LIMITS'] = dict()
            self.config['USAGE'] = dict()
            self.latest_time = datetime.now()
            return

        self.cfg_file = cfg_file 
        self.config = ConfigParser()
        self.config.read(self.cfg_file)
        if 'LIMITS' not in self.config.sections():
            self.config['USAGE'] = dict()

        if 'USAGE' in self.config.sections():
            if 'latest_time' in self.config['USAGE']:
                lt = self.config['USAGE']['latest_time']
                self.latest_time = datetime.fromisoformat(lt)
            else:
                self.latest_time = datetime.now()

            for key, value in self.config['USAGE'].items():
                unit = RateLimiter.parse_unit(key)
                if unit != None and value.isdigit():
                    self.usage[unit] = int(value)
                elif key == 'latest_time':
                    continue
                elif unit == None:
                    print(f'paramater {key} not valid')
                elif not value.isdigit():
                    print(f'value of {key} must be a positive integer')
        else:
            self.latest_time = datetime.now()
            self.config['USAGE'] = dict()
            self.__init_usage()


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        self.write_usage()


    def __init_usage(self) -> None:
        """Initializes values for the usage of time units in limits"""
        for param in self.config['LIMITS']:
            if (unit := RateLimiter.parse_unit(param)) != None:
                self.usage[unit] = 0
            else:
                raise Exception(f'unknown time unit in LIMITS: {param}')

    
    def update_limits(self, **kwargs) -> None:
        """Updates the limit values found in the config file
         
        Parameters
        ----------
        **kwargs
           The name(s) of a unit(s) found in the Units enumeration
           class and an integer to update the limit of request of said
           unit.
        """

        for key, value in kwargs.items():
            # should be checking for int
            if RateLimiter.parse_unit(key) != None and value is int:
                self.config['LIMITS'][key.name] = str(value)
            else:
                # TODO: raise some errors
                continue
        with open(self.cfg_file, 'w') as configfile:
            self.config.write(configfile)


    def write_usage(self) -> None:
        """Writes the usage amounts in the config file """
        self.config['USAGE']['latest_time'] = str(self.latest_time)
        for key, value in self.usage.items():
            self.config['USAGE'][key.name] = str(value)
        with open(self.cfg_file, 'w') as configfile:
            self.config.write(configfile)


    def cooldown(self) -> float:
        """ gives the amount of seconds until you can make your next
        request"""
        
        for unit in self.config['LIMITS']:
            u = RateLimiter.parse_unit(unit)
            if u != None and self.usage[u] >= int(self.config['LIMITS'][unit]):
                return self.__calculate_cooldown(u)

        return 0.0


    def __is_after(self, unit: Units) -> bool:
        """Determines if the current time is after the time of the
        latest request

        Parameters
        ----------
        unit : Units
            the unit of time/accurnacy that the function will compare
            the current time and latest request time up to
        """

        latest_time = self.latest_time.timetuple()
        current_time = datetime.now().timetuple()

        for i in range(unit.value):
            if current_time[i] < latest_time[i]:
                return False
        else:
            if current_time[i+1] == latest_time[i+1]:
                return False
        return True


    def __reset_usage(self, unit: Units) -> None:
        """Resets the usage amounts of units of time larger or equal to
        unit"""

        for u in reversed(Units):
            if u not in self.usage:
                continue
            self.usage[u] = 0
            if u == unit:
                break


    def __calculate_cooldown(self, unit: Units) -> float:
        """finds the amount of time until the next increment in the
        unit of time from the latest request time"""

        next_increment = [*datetime.min.timetuple()][:6]
        for u in Units:
            next_increment[u.value] = self.latest_time.timetuple()[u.value]
        next_increment = datetime(*next_increment)

        if unit == Units.YEAR:
            next_increment += timedelta(years=1)
        elif unit == Units.MONTH:
            next_increment += timedelta(months=1)
        elif unit == Units.DAY:
            next_increment += timedelta(days=1)
        elif unit == Units.HOUR:
            next_increment += timedelta(hours=1)
        elif unit == Units.MINUTE:
            next_increment += timedelta(minutes=1)
        elif unit == Units.SECOND:
            next_increment += timedelta(seconds=1)

        return (next_increment - self.latest_time).total_seconds()


    def request(self, func, *args, **kwargs):
        """Calls the provided function and increments usage

        Parameters
        ----------
        func : function
            the function to be called in the request
        args
            positional arguments given to the function
        kwargs
            keyword arguments given to the function
        """
        try:
            output = func(*args, **kwargs)
            for unit in self.usage:
                if self.__is_after(unit):
                    self.__reset_usage(unit)
                self.usage[unit] += 1

            self.latest_time = datetime.now()
        except Exception as e:
            self.write_usage()
            raise e

        return output

    def parse_unit(string: str) -> Units:
        """Converts a string to its respective Units type

        Parameters
        ---------
        string : str
            the string to be converted
        """
        if string == 'year':
            return Units.YEAR
        elif string == 'month':
            return Units.MONTH
        elif string == 'day':
            return Units.DAY
        elif string == 'hour':
            return Units.HOUR
        elif string == 'minute':
            return Units.MINUTE
        elif string == 'second':
            return Units.SECOND
        else:
            return None

