r"""Utility functions that are used across modules.

Ensure these do not reference any function from colors.py. If a function does need to reference another function from colors.py,
add it in that file.

Public utility functions should be added to documentation in the '/docs/_templates/overrides/tropycal.utils.rst' file."""

import os, sys
import math
import numpy as np
import pandas as pd
from datetime import datetime as dt,timedelta
import requests
import urllib
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib as mlib
from matplotlib import path
import warnings
import scipy.interpolate as interp
import re
import shapefile
import zipfile
from io import StringIO, BytesIO

from .. import constants

#===========================================================================================================
# Public utilities
# These are used internally and have use externally. Add these to documentation.
#===========================================================================================================

def wind_to_category(wind_speed):
    
    r"""
    Convert sustained wind speed in knots to Saffir-Simpson Hurricane Wind Scale category.
    
    Parameters
    ----------
    wind_speed : int
        Sustained wind speed in knots.
    
    Returns
    -------
    int
        Category corresponding to the sustained wind. 0 is tropical storm, -1 is tropical depression.
    """
    
    #Category 5 hurricane
    if wind_speed >= 137:
        return 5
    
    #Category 4 hurricane
    elif wind_speed >= 113:
        return 4
    
    #Category 3 hurricane
    elif wind_speed >= 96:
        return 3
    
    #Category 2 hurricane
    elif wind_speed >= 83:
        return 2
    
    #Category 1 hurricane
    elif wind_speed >= 64:
        return 1
    
    #Tropical storm
    elif wind_speed >= 34:
        return 0
    
    #Tropical depression
    else:
        return -1

def category_to_wind(category):
    
    r"""
    Convert Saffir-Simpson Hurricane Wind Scale category to minimum threshold sustained wind speed in knots.
    
    Parameters
    ----------
    category : int
        Saffir-Simpson Hurricane Wind Scale category. Use 0 for tropical storm, -1 for tropical depression.
    
    Returns
    -------
    int
        Sustained wind speed in knots corresponding to the minimum threshold of the requested category.
    """
    
    #Construct dictionary of thresholds
    conversion = {-1:5,
                  0:34,
                  1:64,
                  2:83,
                  3:96,
                  4:113,
                  5:137}
    
    #Return category
    return conversion.get(category,np.nan)

def classify_subtropical(storm_type):
    
    r"""
    Determine whether a tropical cyclone was purely subtropical.
    
    Parameters
    ----------
    storm_type : list or numpy.ndarray
        List or array containing storm types.
    
    Returns
    -------
    bool
        Boolean identifying whether the tropical cyclone was purely subtropical.
    """
    
    #Ensure storm_type is a numpy array
    storm_type_check = np.array(storm_type)
    
    #Ensure all storm types are uppercase
    storm_track_check = [i.upper() for i in storm_type_check]
    
    #Check for subtropical depression status
    if 'SD' in storm_type_check:
        if 'SD' in storm_type_check and True not in np.isin(storm_type_check,['TD','TS','HU']):
            return True
    
    #Check for subtropical storm status
    if 'SS' in storm_type_check and True not in np.isin(storm_type_check,['TD','TS','HU']):
        return True
    
    #Otherwise, it was a tropical cyclone at some point in its life cycle
    else:
        return False

def get_storm_classification(wind_speed,subtropical_flag,basin):
    
    r"""
    Retrieve the tropical cyclone classification given its subtropical status and current basin.
    
    These strings take the format of "Tropical Storm", "Hurricane", "Typhoon", etc.
    
    Parameters
    ----------
    wind_speed : int
        Integer denoting sustained wind speed in knots.
    subtropical_flag : bool
        Boolean denoting whether the cyclone is subtropical or not.
    basin : str
        String denoting basin in which the tropical cyclone is located.
    
    Returns
    -------
    str
        String denoting the classification of the tropical cyclone.
    
    Notes
    -----
    
    .. warning::

        This function currently does not differentiate between 1-minute, 3-minute and 10-minute sustained wind speeds.
    
    """
    
    #North Atlantic and East Pacific basins
    if basin in ['north_atlantic','east_pacific']:
        if wind_speed == 0:
            return "Unknown"
        elif wind_speed < 34:
            if subtropical_flag == True:
                return "Subtropical Depression"
            else:
                return "Tropical Depression"
        elif wind_speed < 63:
            if subtropical_flag == True:
                return "Subtropical Storm"
            else:
                return "Tropical Storm"
        else:
            return "Hurricane"
    
    #West Pacific basin
    elif basin == 'west_pacific':
        if wind_speed == 0:
            return "Unknown"
        elif wind_speed < 34:
            if subtropical_flag == True:
                return "Subtropical Depression"
            else:
                return "Tropical Depression"
        elif wind_speed < 63:
            if subtropical_flag == True:
                return "Subtropical Storm"
            else:
                return "Tropical Storm"
        elif wind_speed < 130:
            return "Typhoon"
        else:
            return "Super Typhoon"
    
    #Australia and South Pacific basins
    elif basin == 'australia' or basin == 'south_pacific':
        if wind_speed == 0:
            return "Unknown"
        elif wind_speed < 63:
            return "Tropical Cyclone"
        else:
            return "Severe Tropical Cyclone"
    
    #North Indian Ocean
    elif basin == 'north_indian':
        if wind_speed == 0:
            return "Unknown"
        elif wind_speed < 28:
            return "Depression"
        elif wind_speed < 34:
            return "Deep Depression"
        elif wind_speed < 48:
            return "Cyclonic Storm"
        elif wind_speed < 64:
            return "Severe Cyclonic Storm"
        elif wind_speed < 90:
            return "Very Severe Cyclonic Storm"
        elif wind_speed < 120:
            return "Extremely Severe Cyclonic Storm"
        else:
            return "Super Cyclonic Storm"
    
    #South Indian Ocean
    elif basin == 'south_indian':
        if wind_speed == 0:
            return "Unknown"
        elif wind_speed < 28:
            return "Tropical Disturbance"
        elif wind_speed < 34:
            return "Tropical Depression"
        elif wind_speed < 48:
            return "Moderate Tropical Storm"
        elif wind_speed < 64:
            return "Severe Tropical Storm"
        elif wind_speed < 90:
            return "Tropical Cyclone"
        elif wind_speed < 115:
            return "Intense Tropical Cyclone"
        else:
            return "Very Intense Tropical Cyclone"
    
    #Otherwise, return a generic "Cyclone" classification
    else:
        return "Cyclone"

def get_storm_type(wind_speed,subtropical_flag):
    
    r"""
    Retrieve the 2-character tropical cyclone type (e.g., "TD", "TS", "HU") given its subtropical status.
    
    Parameters
    ----------
    wind_speed : int
        Integer denoting sustained wind speed in knots.
    subtropical_flag : bool
        Boolean denoting whether the cyclone is subtropical or not.
    
    Returns
    -------
    str
        String denoting the tropical cyclone type.
    
    Notes
    -----
    The available types and their descriptions are as follows:
    
    .. list-table:: 
       :widths: 25 75
       :header-rows: 1

       * - Property
         - Description
       * - TD
         - Tropical Depression
       * - TS
         - Tropical Storm
       * - HU
         - Hurricane
       * - SD
         - Subtropical Depression
       * - SS
         - Subtropical Storm
    """
    
    #Tropical depression
    if wind_speed < 34:
        if subtropical_flag == True:
            return "SD"
        else:
            return "TD"
    
    #Tropical storm
    elif wind_speed < 63:
        if subtropical_flag == True:
            return "SS"
        else:
            return "TS"
    
    #Hurricane
    else:
        return "HU"

def get_basin(lat,lon,source_basin=""):
    
    r"""
    Returns the current basin of the tropical cyclone.
    
    Parameters
    ----------
    lat : int or float
        Latitude of the storm.
    lon : int or float
        Longitude of the storm.
    
    Other Parameters
    ----------------
    source_basin : str, optional
        String representing the origin storm basin (e.g., "north_atlantic", "east_pacific").
    
    Returns
    -------
    str
        String representing the current basin (e.g., "north_atlantic", "east_pacific").
    
    Notes
    -----
    For storms in the North Atlantic or East Pacific basin, ``source_basin`` must be provided. This is because storms located over Mexico or Central America could be in either basin depending on where they originated (e.g., storms originated in the Atlantic basin are considered to be within the Atlantic basin while over Mexico or Central America until emerging in the Pacific Ocean).
    """
    
    #Error check
    if isinstance(lat,(int,np.int,np.integer,float,np.floating)) == False:
        msg = "\"lat\" must be of type int or float."
        raise TypeError(msg)
    if isinstance(lon,(int,np.int,np.integer,float,np.floating)) == False:
        msg = "\"lon\" must be of type int or float."
        raise TypeError(msg)
    
    #Fix longitude
    if lon < 0.0: lon = lon + 360.0
    
    #Northern hemisphere check
    if lat >= 0.0:
        
        if lon < 100.0:
            if lat < 40.0:
                return "north_indian"
            else:
                if lon < 70.0:
                    return "north_atlantic"
                else:
                    return "west_pacific"
        elif lon <= 180.0:
            return "west_pacific"
        else:
            if source_basin == "north_atlantic":
                if constants.PATH_PACIFIC.contains_point((lat,lon)):
                    return "east_pacific"
                else:
                    return "north_atlantic"
            elif source_basin == "east_pacific":
                if constants.PATH_ATLANTIC.contains_point((lat,lon)):
                    return "north_atlantic"
                else:
                    return "east_pacific"
            else:
                msg = "Cannot determine whether storm is in North Atlantic or East Pacific basins."
                raise RuntimeError(msg)
    
    #Southern hemisphere check
    else:
        
        if lon < 20.0:
            return "south_atlantic"
        elif lon < 90.0:
            return "south_indian"
        elif lon < 160.0:
            return "australia"
        elif lon < 280.0:
            return "south_pacific"
        else:
            return "south_atlantic"

def knots_to_mph(wind_speed):
    
    r"""
    Convert wind from knots to miles per hour, in increments of 5 as used by NHC.
    
    Parameters
    ----------
    wind_speed : int
        Sustained wind in knots.
    
    Returns
    -------
    int
        Sustained wind in miles per hour.
    """
    
    #Ensure input is rounded down to nearest multiple of 5
    wind_speed = wind_speed - (wind_speed % 5)

    #Define knots and mph conversions
    kts = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185]
    mphs = [0,10,15,20,25,30,35,40,45,50,60,65,70,75,80,85,90,100,105,110,115,120,125,130,140,145,150,155,160,165,175,180,185,190,195,200,205,210]
    
    #If value is in list, return converted value
    if wind_speed in kts:
        return mphs[kts.index(wind_speed)]
    
    #Otherwise, return original value
    return wind_speed

def accumulated_cyclone_energy(wind_speed,hours=6):
    
    r"""
    Calculate Accumulated Cyclone Energy (ACE) based on sustained wind speed in knots.
    
    Parameters
    ----------
    wind_speed : int or list, numpy.ndarray
        Sustained wind in knots.
    hours : int, optional
        Duration in hours over which the sustained wind was observed. Default is 6 hours.
    
    Returns
    -------
    float
        Accumulated cyclone energy.
    
    Notes
    -----
    
    As defined in `Bell et al. (2000)`_, Accumulated Cyclone Energy (ACE) is calculated as follows:
    
    .. math:: ACE = 10^{-4} \sum v^{2}_{max}
    
    As shown above, ACE is the sum of the squares of the estimated maximum sustained wind speed (in knots). By default, this assumes data is provided every 6 hours, as is the standard in HURDATv2 and NHC's Best Track, though this function provides an option to use a different hour duration.
    
    .. _Bell et al. (2000): https://journals.ametsoc.org/view/journals/bams/81/6/1520-0477_2000_81_s1_caf_2_0_co_2.xml
    """
    
    #Determine types
    if isinstance(wind_speed,(np.ndarray,list)):
        wind_speed = np.copy(wind_speed)
    
    #Calculate ACE
    ace = ((10**-4) * (wind_speed**2)) * (hours/6.0)
    
    #Coerce to zero if wind speed less than TS force
    if isinstance(ace,(np.ndarray,list)):
        ace[wind_speed < 34] = 0.0
        return np.round(ace,4)
    else:
        if wind_speed < 34: ace = 0.0
        return round(ace,4)

def dropsonde_mslp_estimate(mslp,surface_wind):
    
    r"""
    Apply a NHC rule of thumb for estimating a TC's minimum central MSLP. This is intended for a dropsonde released in the eye, accounting for drifting by factoring in the surface wind in knots.
    
    Parameters
    ----------
    mslp : int or float
        Dropsonde surface MSLP, in hPa.
    surface_wind : int or float
        Surface wind as measured by the dropsonde. This **must** be surface wind; this cannot be substituted by a level just above the surface.
    
    Returns
    -------
    float
        Estimated TC minimum central MSLP using the NHC estimation method.
    
    Notes
    -----
    Source is from NHC presentation:
    https://www.nhc.noaa.gov/outreach/presentations/nhc2013_aircraftData.pdf
    """
    
    return mslp - (surface_wind / 10.0)

def get_two_current():
    
    r"""
    Retrieve the latest NHC Tropical Weather Outlook (TWO).
    
    Returns
    -------
    dict
        A dictionary of shapefiles for points, areas and lines.
    
    Notes
    -----
    The shapefiles returned are modified versions of Cartopy's BasicReader, allowing to read in shapefiles directly from URL without having to download the shapefile locally first.
    """
    
    #Retrieve NHC shapefiles for development areas
    shapefiles = {}
    for name in ['areas','lines','points']:

        try:
            #Read in shapefile zip from NHC
            url = 'https://www.nhc.noaa.gov/xgtwo/gtwo_shapefiles.zip'
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            file_like_object = BytesIO(response.read())
            tar = zipfile.ZipFile(file_like_object)

            #Get file list (points, areas)
            members = '\n'.join([i for i in tar.namelist()])
            nums = "[0123456789]"
            search_pattern = f'gtwo_{name}_20{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}.shp'
            pattern = re.compile(search_pattern)
            filelist = pattern.findall(members)
            files = []
            for file in filelist:
                if file not in files: files.append(file.split(".shp")[0]) #remove duplicates

            #Retrieve necessary components for shapefile
            members = tar.namelist()
            members_names = [i for i in members]
            data = {'shp':0,'dbf':0,'prj':0,'shx':0}
            for key in data.keys():
                idx = members_names.index(files[0]+"."+key)
                data[key] = BytesIO(tar.read(members[idx]))

            #Read in shapefile
            orig_reader = shapefile.Reader(shp=data['shp'], dbf=data['dbf'], prj=data['prj'], shx=data['shx'])
            shapefiles[name] = BasicReader(orig_reader)
        except:
            shapefiles[name] = None
    
    return shapefiles
    
def get_two_archive(time):
    
    r"""
    Retrieve an archived NHC Tropical Weather Outlook (TWO). If none available within 30 hours of the specified date, an empty dict is returned.
    
    Parameters
    ----------
    time : datetime
        Valid time for archived shapefile.
    
    Returns
    -------
    dict
        A dictionary of shapefiles for points, areas and lines.
    
    Notes
    -----
    The shapefiles returned are modified versions of Cartopy's BasicReader, allowing to read in shapefiles directly from URL without having to download the shapefile locally first.
    
    TWO shapefiles are available courtesy of the National Hurricane Center beginning 28 July 2010.
    """
    
    #Find closest NHC shapefile if within 24 hours
    url = 'https://www.nhc.noaa.gov/gis/archive_gtwo.php'
    page = requests.get(url).text
    content = page.split("\n")
    files = []
    for line in content:
        if '<a href="gtwo/archive/2' in line:
            filename = line.split('zip">')[1]
            filename = filename.split("</a>")[0]
            files.append(filename)
    del content
    dates = [dt.strptime(i.split("_")[0],'%Y%m%d%H%M') for i in files]
    diff = [(time-i).total_seconds()/3600 for i in dates]
    diff = [i for i in diff if i >= 0]

    #Continue if less than 24 hours difference
    if np.nanmin(diff) <= 30:
        two_date = dates[diff.index(np.nanmin(diff))].strftime('%Y%m%d%H%M')

        #Retrieve NHC shapefiles for development areas
        shapefiles = {}
        for name in ['areas','lines','points']:

            try:
                #Read in shapefile zip from NHC
                url = f'https://www.nhc.noaa.gov/gis/gtwo/archive/{two_date}_gtwo.zip'
                request = urllib.request.Request(url)
                response = urllib.request.urlopen(request)
                file_like_object = BytesIO(response.read())
                tar = zipfile.ZipFile(file_like_object)

                #Get file list (points, areas)
                members = '\n'.join([i for i in tar.namelist()])
                nums = "[0123456789]"
                search_pattern = f'gtwo_{name}_20{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}{nums}.shp'
                pattern = re.compile(search_pattern)
                filelist = pattern.findall(members)
                files = []
                for file in filelist:
                    if file not in files: files.append(file.split(".shp")[0]) #remove duplicates

                #Retrieve necessary components for shapefile
                members = tar.namelist()
                members_names = [i for i in members]
                data = {'shp':0,'dbf':0,'prj':0,'shx':0}
                for key in data.keys():
                    idx = members_names.index(files[0]+"."+key)
                    data[key] = BytesIO(tar.read(members[idx]))

                #Read in shapefile
                orig_reader = shapefile.Reader(shp=data['shp'], dbf=data['dbf'], prj=data['prj'], shx=data['shx'])
                shapefiles[name] = BasicReader(orig_reader)
            except:
                shapefiles[name] = None
    else:
        shapefiles = {'areas':None,'lines':None,'points':None}
    
    return shapefiles

def nhc_cone_radii(year,basin,forecast_hour=None):
    
    r"""
    Retrieve the official NHC Cone of Uncertainty radii by basin, year and forecast hour(s). Units are in nautical miles.
    
    Parameters
    ----------
    year : int
        Valid year for cone of uncertainty radii.
    basin : str
        Basin for cone of uncertainty radii. If basin is invalid, return value will be an empty dict. Please refer to :ref:`options-domain` for available basin options.
    forecast_hour : int or list, optional
        Forecast hour(s) to retrieve the cone of uncertainty for. If empty, all available forecast hours will be retrieved.
    
    Returns
    -------
    dict
        Dictionary with forecast hour(s) as the keys, and the cone radius in nautical miles for each respective forecast hour as the values.
    
    Notes
    -----
    1. NHC cone radii are available beginning 2008 onward. Radii for years before 2008 will be defaulted to 2008, and if the current year's radii are not available yet, the radii for the most recent year will be returned.
    
    2. NHC began producing cone radii for forecast hour 60 in 2020. Years before 2020 do not have a forecast hour 60.
    """
    
    #Source: https://www.nhc.noaa.gov/verification/verify3.shtml
    #Source 2: https://www.nhc.noaa.gov/aboutcone.shtml
    #Radii are in nautical miles
    cone_climo_hr = [3,12,24,36,48,72,96,120]
    
    #Basin check
    if basin not in ['north_atlantic','east_pacific']:
        return {}
    
    #Fix for 2020 and later that incorporates 60 hour forecasts
    if year >= 2020:
        cone_climo_hr = [3,12,24,36,48,60,72,96,120]
    
    #Forecast hour check
    if forecast_hour is None:
        forecast_hour = cone_climo_hr
    elif isinstance(forecast_hour,int) == True:
        if forecast_hour not in cone_climo_hr:
            raise ValueError(f"Forecast hour {forecast_hour} is invalid. Available forecast hours for {year} are: {cone_climo_hr}")
        else:
            forecast_hour = [forecast_hour]
    elif isinstance(forecast_hour,list) == True:
        forecast_hour = [i for i in forecast_hour if i in cone_climo_hr]
        if len(forecast_hour) == 0:
            raise ValueError(f"Requested forecast hours are invalid. Available forecast hours for {year} are: {cone_climo_hr}")
    else:
        raise TypeError("forecast_hour must be of type int or list")
    
    #Year check
    if year > np.max([k for k in constants.CONE_SIZE_ATL.keys()]):
        year = [k for k in constants.CONE_SIZE_ATL.keys()][0]
        warnings.warn(f"No cone information is available for the requested year. Defaulting to {year} cone.")
    elif year not in constants.CONE_SIZE_ATL.keys():
        year = 2008
        warnings.warn(f"No cone information is available for the requested year. Defaulting to 2008 cone.")
    
    #Retrieve data
    cone_radii = {}
    for hour in list(np.sort(forecast_hour)):
        hour_index = cone_climo_hr.index(hour)
        if basin == 'north_atlantic':
            cone_radii[hour] = constants.CONE_SIZE_ATL[year][hour_index]
        elif basin == 'east_pacific':
            cone_radii[hour] = constants.CONE_SIZE_PAC[year][hour_index]
    
    return cone_radii

def generate_nhc_cone(forecast,basin,shift_lons=False,cone_days=5,cone_year=None,return_xarray=False):

    r"""
    Generates a gridded cone of uncertainty using forecast data from NHC.

    Parameters
    ----------
    forecast : dict
        Dictionary containing forecast data
    basin : str
        Basin for cone of uncertainty radii. Please refer to :ref:`options-domain` for available basin options.
    shift_lons : bool, optional
        If true, grid will be shifted to +0 to +360 degrees longitude. Default is False (-180 to +180 degrees).
    cone_days : int, optional
        Number of forecast days to generate the cone through. Default is 5 days.
    cone_year : int, optional
        Year valid for cone radii. If None, this fuction will attempt to retrieve the year from the forecast dict.
    return_xarray : bool, optional
        If True, returns output as an xarray Dataset. Default is False, returning output as a dictionary.
    
    Returns
    -------
    dict or xarray.Dataset
        Depending on `return_xarray`, returns either a dictionary or an xarray Dataset containing the gridded cone of uncertainty and its accompanying attributes.
    
    Notes
    -----
    Forecast dicts can be retrieved for realtime storm objects using ``RealtimeStorm.get_forecast_realtime()``, and for archived storms using ``Storm.get_nhc_forecast_dict()``.
    """
    
    #Check forecast dict has all required keys
    check_dict = [True if i in forecast.keys() else False for i in ['fhr','lat','lon','init']]
    if False in check_dict:
        raise ValueError("forecast dict must contain keys 'fhr', 'lat', 'lon' and 'init'. You may retrieve a forecast dict for a Storm object through 'storm.get_operational_forecasts()'.")
    
    #Check forecast basin
    if basin not in constants.ALL_BASINS:
        raise ValueError("basin cannot be identified.")

    #Retrieve cone of uncertainty year
    if cone_year is None:
        cone_year = forecast['init'].year
    if cone_year > np.max([k for k in constants.CONE_SIZE_ATL.keys()]):
        cone_year = [k for k in constants.CONE_SIZE_ATL.keys()][0]
        warnings.warn(f"No cone information is available for the requested year. Defaulting to {cone_year} cone.")
    elif cone_year not in constants.CONE_SIZE_ATL.keys():
        cone_year = 2008
        warnings.warn(f"No cone information is available for the requested year. Defaulting to 2008 cone.")

    #Retrieve cone size and hours for given year
    if basin in ['north_atlantic','east_pacific']:
        output = nhc_cone_radii(cone_year,basin)
        cone_climo_hr = [k for k in output.keys()]
        cone_size = [output[k] for k in output.keys()]
    else:
        cone_climo_hr = [3,12,24,36,48,72,96,120]
        cone_size = 0

    #Function for interpolating between 2 times
    def temporal_interpolation(value, orig_times, target_times):
        f = interp.interp1d(orig_times,value)
        ynew = f(target_times)
        return ynew

    #Function for plugging small array into larger array
    def plug_array(small,large,small_coords,large_coords):

        small_lat = np.round(small_coords['lat'],2)
        small_lon = np.round(small_coords['lon'],2)
        large_lat = np.round(large_coords['lat'],2)
        large_lon = np.round(large_coords['lon'],2)

        small_minlat = min(small_lat)
        small_maxlat = max(small_lat)
        small_minlon = min(small_lon)
        small_maxlon = max(small_lon)

        if small_minlat in large_lat:
            minlat = np.where(large_lat==small_minlat)[0][0]
        else:
            minlat = min(large_lat)
        if small_maxlat in large_lat:
            maxlat = np.where(large_lat==small_maxlat)[0][0]
        else:
            maxlat = max(large_lat)
        if small_minlon in large_lon:
            minlon = np.where(large_lon==small_minlon)[0][0]
        else:
            minlon = min(large_lon)
        if small_maxlon in large_lon:
            maxlon = np.where(large_lon==small_maxlon)[0][0]
        else:
            maxlon = max(large_lon)

        large[minlat:maxlat+1,minlon:maxlon+1] = small

        return large

    #Function for finding nearest value in an array
    def findNearest(array,val):
        return array[np.abs(array - val).argmin()]

    #Function for adding a radius surrounding a point
    def add_radius(lats,lons,vlat,vlon,rad):

        #construct new array expanding slightly over rad from lat/lon center
        grid_res = 0.05 #1 degree is approx 111 km
        grid_fac = (rad*4)/111.0

        #Make grid surrounding position coordinate & radius of circle
        nlon = np.arange(findNearest(lons,vlon-grid_fac),findNearest(lons,vlon+grid_fac+grid_res),grid_res)
        nlat = np.arange(findNearest(lats,vlat-grid_fac),findNearest(lats,vlat+grid_fac+grid_res),grid_res)
        lons,lats = np.meshgrid(nlon,nlat)
        return_arr = np.zeros((lons.shape))

        #Calculate distance from vlat/vlon at each gridpoint
        r_earth = 6.371 * 10**6
        dlat = np.subtract(np.radians(lats),np.radians(vlat))
        dlon = np.subtract(np.radians(lons),np.radians(vlon))

        a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lats)) * np.cos(np.radians(vlat)) * np.sin(dlon/2) * np.sin(dlon/2)
        c = 2 * np.arctan(np.sqrt(a), np.sqrt(1-a));
        dist = (r_earth * c)/1000.0
        dist = dist * 0.621371 #to miles
        dist = dist * 0.868976 #to nautical miles

        #Mask out values less than radius
        return_arr[dist <= rad] = 1

        #Attach small array into larger subset array
        small_coords = {'lat':nlat,'lon':nlon}

        return return_arr, small_coords

    #--------------------------------------------------------------------

    #Check if fhr3 is available, then get forecast data
    flag_12 = 0
    if forecast['fhr'][0] == 12:
        flag_12 = 1
        cone_climo_hr = cone_climo_hr[1:]
        fcst_lon = forecast['lon']
        fcst_lat = forecast['lat']
        fhr = forecast['fhr']
        t = np.array(forecast['fhr'])/6.0
        subtract_by = t[0]
        t = t - t[0]
        interp_fhr_idx = np.arange(t[0],t[-1]+0.1,0.1) - t[0]
    elif 3 in forecast['fhr'] and 1 in forecast['fhr'] and 0 in forecast['fhr']:
        fcst_lon = forecast['lon'][2:]
        fcst_lat = forecast['lat'][2:]
        fhr = forecast['fhr'][2:]
        t = np.array(fhr)/6.0
        interp_fhr_idx = np.arange(t[0],t[-1]+0.01,0.1)
    elif 3 in forecast['fhr'] and 0 in forecast['fhr']:
        idx = np.array([i for i,j in enumerate(forecast['fhr']) if j in cone_climo_hr])
        fcst_lon = np.array(forecast['lon'])[idx]
        fcst_lat = np.array(forecast['lat'])[idx]
        fhr = np.array(forecast['fhr'])[idx]
        t = np.array(fhr)/6.0
        interp_fhr_idx = np.arange(t[0],t[-1]+0.01,0.1)
    elif forecast['fhr'][1] < 12:
        cone_climo_hr[0] = 0
        fcst_lon = [forecast['lon'][0]]+forecast['lon'][2:]
        fcst_lat = [forecast['lat'][0]]+forecast['lat'][2:]
        fhr = [forecast['fhr'][0]]+forecast['fhr'][2:]
        t = np.array(fhr)/6.0
        interp_fhr_idx = np.arange(t[0]/6.0,t[-1]+0.1,0.1)
    else:
        cone_climo_hr[0] = 0
        fcst_lon = forecast['lon']
        fcst_lat = forecast['lat']
        fhr = forecast['fhr']
        t = np.array(fhr)/6.0
        interp_fhr_idx = np.arange(t[0],t[-1]+0.1,0.1)

    #Determine index of forecast day cap
    if (cone_days*24) in fhr:
        cone_day_cap = list(fhr).index(cone_days*24)+1
        fcst_lon = fcst_lon[:cone_day_cap]
        fcst_lat = fcst_lat[:cone_day_cap]
        fhr = fhr[:cone_day_cap]
        t = np.array(fhr)/6.0
        interp_fhr_idx = np.arange(interp_fhr_idx[0],t[-1]+0.1,0.1)
    else:
        cone_day_cap = len(fhr)

    #Account for dateline
    if shift_lons == True:
        temp_lon = np.array(fcst_lon)
        temp_lon[temp_lon<0] = temp_lon[temp_lon<0]+360.0
        fcst_lon = temp_lon.tolist()

    #Interpolate forecast data temporally and spatially
    interp_kind = 'quadratic'
    if len(t) == 2: interp_kind = 'linear' #Interpolate linearly if only 2 forecast points
    x1 = interp.interp1d(t,fcst_lon,kind=interp_kind)
    y1 = interp.interp1d(t,fcst_lat,kind=interp_kind)
    interp_fhr = interp_fhr_idx * 6
    interp_lon = x1(interp_fhr_idx)
    interp_lat = y1(interp_fhr_idx)

    #Return if no cone specified
    if cone_size == 0:
        return_dict = {'center_lon':interp_lon,'center_lat':interp_lat}
        if return_xarray:
            import xarray as xr
            return xr.Dataset(return_dict)
        else:
            return return_dict

    #Interpolate cone radius temporally
    cone_climo_hr = cone_climo_hr[:cone_day_cap]
    cone_size = cone_size[:cone_day_cap]

    cone_climo_fhrs = np.array(cone_climo_hr)
    if flag_12 == 1:
        interp_fhr += (subtract_by*6.0)
        cone_climo_fhrs = cone_climo_fhrs[1:]
    idxs = np.nonzero(np.in1d(np.array(fhr),np.array(cone_climo_hr)))
    temp_arr = np.array(cone_size)[idxs]
    interp_rad = np.apply_along_axis(lambda n: temporal_interpolation(n,fhr,interp_fhr),axis=0,arr=temp_arr)

    #Initialize 0.05 degree grid
    gridlats = np.arange(min(interp_lat)-7,max(interp_lat)+7,0.05)
    gridlons = np.arange(min(interp_lon)-7,max(interp_lon)+7,0.05)
    gridlons2d,gridlats2d = np.meshgrid(gridlons,gridlats)

    #Iterate through fhr, calculate cone & add into grid
    large_coords = {'lat':gridlats,'lon':gridlons}
    griddata = np.zeros((gridlats2d.shape))
    for i,(ilat,ilon,irad) in enumerate(zip(interp_lat,interp_lon,interp_rad)):
        temp_grid, small_coords = add_radius(gridlats,gridlons,ilat,ilon,irad)
        plug_grid = np.zeros((griddata.shape))
        plug_grid = plug_array(temp_grid,plug_grid,small_coords,large_coords)
        griddata = np.maximum(griddata,plug_grid)
    
    if return_xarray:
        import xarray as xr
        cone = xr.DataArray(griddata,coords=[gridlats,gridlons],dims=['grid_lat','grid_lon'])
        return_ds = {
            'cone':cone,
            'center_lon':interp_lon,
            'center_lat':interp_lat
        }
        return_ds = xr.Dataset(return_ds)
        return_ds.attrs['year'] = cone_year
        return return_ds
    
    else:
        return_dict = {'lat':gridlats,'lon':gridlons,'lat2d':gridlats2d,'lon2d':gridlons2d,'cone':griddata,
                   'center_lon':interp_lon,'center_lat':interp_lat,'year':cone_year}
        return return_dict

def calc_ensemble_ellipse(member_lons,member_lats):
    
    r"""
    Calculate an ellipse representing ensemble member location spread. This function follows the methodology of Hamill et al. (2011).
    
    Parameters
    ----------
    member_lons : list
        List containing longitudes of ensemble members valid at a single time.
    member_lats : list
        List containing latitudes of ensemble members valid at a single time.
    
    Returns
    -------
    dict
        Dictionary containing the longitude and latitude of the ellipse.
    
    Notes
    -----
    The ensemble ellipse used in this function follows the methodology of `Hamill et al. (2011)`_, denoting the spread in ensemble member cyclone positions. The size of the ellipse is calculated to contain 90% of ensemble members at any given time. This ellipse can be used to determine the primary type of ensemble variability:

    * **Along-track variability** - if the major axis of the ellipse is parallel to the ensemble mean motion vector.
    * **Across-track variability** - if the major axis of the ellipse is normal to the ensemble mean motion vector.

    .. _Hamill et al. (2011): https://doi.org/10.1175/2010MWR3456.1
    
    This code is adapted from NCAR Command Language (NCL) code courtesy of Ryan Torn and Thomas Hamill.
    """
    
    #Compute ensemble mean lon & lat
    mean_lon = np.average(member_lons)
    mean_lat = np.average(member_lats)

    Pb = [[0,0],[0,0]]
    for i in range(len(member_lats)):
        Pb[0][0] = Pb[0][0] + (member_lons[i]-mean_lon) * (member_lons[i]-mean_lon)
        Pb[1][1] = Pb[1][1] + (member_lats[i]-mean_lat) * (member_lats[i]-mean_lat)
        Pb[1][0] = Pb[1][0] + (member_lats[i]-mean_lat) * (member_lons[i]-mean_lon)
    Pb[0][1] = Pb[1][0]
    Pb = np.array(Pb) / float(len(member_lats)-1)

    rho = Pb[1][0] / (np.sqrt(Pb[0][0]) * np.sqrt(Pb[1][1]))
    sigmax = np.sqrt(Pb[0][0])
    sigmay = np.sqrt(Pb[1][1])
    fac = 1.0 / (2.0 * (1 - rho**2))

    #Calculate lon & lat coordinates of ellipse
    ellipse_lon = []
    ellipse_lat = []
    increment = np.pi/180.0
    for radians in np.arange(0,(2.0*np.pi)+increment,increment):
        xstart = np.cos(radians)
        ystart = np.sin(radians)

        for rdistance in np.arange(0.,2400.):
            xloc = xstart * rdistance/80.0
            yloc = ystart * rdistance/80.0
            dist = np.sqrt(xloc * xloc + yloc * yloc)
            prob = np.exp(-1.0 * fac * ((xloc/sigmax)**2 + (yloc/sigmay)**2 - 2.0 * rho * (xloc/sigmax)*(yloc/sigmay)))
            if prob < 0.256:
                ellipse_lon.append(xloc + mean_lon)
                ellipse_lat.append(yloc + mean_lat)
                break

    #Return ellipse data
    return {'ellipse_lon':ellipse_lon, 'ellipse_lat':ellipse_lat}

def create_storm_dict(filepath,storm_name,storm_id,delimiter=',',time_format='%Y%m%d%H',**kwargs):
    
    r"""
    Creates a storm dict from custom user-provided data.
    
    Parameters
    ----------
    filepath : str
        Relative or absolute file path containing custom storm data.
    storm_name : str
        Storm name for custom storm entry.
    storm_id : str
        Storm ID for custom storm entry.
    
    Other Parameters
    ----------------
    delimiter : str
        Delimiter separating columns for text files. Default is ",".
    time_format : str
        Time format for which to convert times to Datetime objects. Default is ``"%Y%m%d%H"`` (e.g., ``"2015070112"`` for 1200 UTC 1 July 2015).
    time_header : str
        Name of time dimension. If not provided, function will attempt to locate it internally.
    lat_header : str
        Name of latitude dimension. If not provided, function will attempt to locate it internally.
    lon_header : str
        Name of longitude dimension. If not provided, function will attempt to locate it internally.
    vmax_header : str
        Name of maximum sustained wind (knots) dimension. If not provided, function will attempt to locate it internally.
    mslp_header : str
        Name of minimum MSLP (hPa) dimension. If not provided, function will attempt to locate it internally.
    type_header : str
        Name of storm type dimension. If not provided, function will attempt to locate it internally. If not part of entry data, storm type will be derived based on provided wind speed values.
    
    Returns
    -------
    dict
        Dictionary containing formatted custom storm data.
    
    Notes
    -----
    This function creates a formatted storm data dictionary using custom user-provided data. The constraints for the parser are as follows:
    
    1. Rows that begin with a ``#`` or ``\`` are automatically ignored.
    2. The first non-commented row must be a header row.
    3. The header row must contain entries for time, latitude, longitude, maximum sustained wind (knots), and minimum MSLP (hPa). The order of these columns does not matter.
    4. Preferred header names are "date", "lat", "lon", "vmax" and "mslp" for the main 5 categories, but custom header names can be provided. Refer to the "Other Parameters" section above.
    5. Providing a "type" column (e.g., "TS", "HU", "EX") is not required, but is recommended especially if dealing with subtropical or non-tropical types.
    
    Below is an example file which we'll call ``data.txt``::

        # The row below is a header row. The order of the columns doesn't matter.
        date,lat,lon,vmax,mslp,type
        2021080518,19.4,-59.9,25,1014,DB
        2021080600,19.7,-60.2,25,1014,DB
        2021080606,20.1,-60.5,30,1012,DB
        2021080612,20.5,-60.8,30,1011,TD
        2021080618,20.7,-61.3,30,1011,TD
        2021080700,20.8,-61.8,35,1008,TS
        2021080706,20.8,-62.6,35,1007,TS
        2021080712,21.0,-63.3,40,1004,TS
        2021080718,21.3,-64.1,45,1002,TS
        2021080800,21.6,-65.1,55,998,TS
        2021080806,22.0,-66.1,60,994,TS
        2021080812,22.5,-66.9,65,989,HU
        2021080818,23.2,-67.4,65,988,HU
        2021080900,23.9,-67.6,60,992,TS
        2021080906,25.0,-67.5,55,994,TS
        2021080912,26.5,-67.1,55,993,TS
        2021080918,28.0,-66.4,50,992,TS
        2021081000,29.5,-65.6,50,994,TS
        2021081006,31.4,-64.0,45,996,TS
        2021081012,33.4,-62.0,45,997,EX
        2021081018,35.4,-59.5,50,997,EX
    
    Reading it into the parser returns the following dict:
    
    >>> from tropycal import utils
    >>> storm_dict = utils.create_storm_dict(filename='data.txt', storm_name='Test', storm_id='AL502021')
    >>> print(storm_dict)
    {'id': 'AL502021',
     'operational_id': 'AL502021',
     'name': 'Test',
     'source_info': 'Custom User Data',
     'source': 'custom',
     'date': [datetime.datetime(2021, 8, 5, 18, 0),
              datetime.datetime(2021, 8, 6, 0, 0),
              ....
              datetime.datetime(2021, 8, 10, 12, 0),
              datetime.datetime(2021, 8, 10, 18, 0)],
     'extra_obs': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     'special': ['','',....,'',''],
     'type': ['DB','DB','DB','TD','TD','TS','TS','TS','TS','TS','TS','HU','HU','TS','TS','TS','TS','TS','TS','EX','EX'],
     'lat': [19.4,19.7,20.1,20.5,20.7,20.8,20.8,21.0,21.3,21.6,22.0,22.5,23.2,23.9,25.0,26.5,28.0,29.5,31.4,33.4,35.4],
     'lon': [-59.9,-60.2,-60.5,-60.8,-61.3,-61.8,-62.6,-63.3,-64.1,-65.1,-66.1,-66.9,-67.4,-67.6,-67.5,-67.1,-66.4,-65.6,-64.0,-62.0,-59.5],
     'vmax': [25.0,25.0,30.0,30.0,30.0,35.0,35.0,40.0,45.0,55.0,60.0,65.0,65.0,60.0,55.0,55.0,50.0,50.0,45.0,45.0,50.0],
     'mslp': [1014,1014,1012,1011,1011,1008,1007,1004,1002,998,994,989,988,992,994,993,992,994,996,997,997],
     'wmo_basin': ['north_atlantic','north_atlantic',....,'north_atlantic','north_atlantic'],
     'ace': 3.7825,
     'basin': 'north_atlantic',
     'year': 2021,
     'season': 2021}
    
    This custom data can then be plugged into a Storm object:
    
    >>> from tropycal import tracks
    >>> storm = tracks.Storm(storm_dict)
    >>> print(storm)
    <tropycal.tracks.Storm>
    Storm Summary:
        Maximum Wind:      65 knots
        Minimum Pressure:  988 hPa
        Start Date:        1200 UTC 06 August 2021
        End Date:          0600 UTC 10 August 2021
    .
    Variables:
        date        (datetime) [2021-08-05 18:00:00 .... 2021-08-10 18:00:00]
        extra_obs   (int32) [0 .... 0]
        special     (str) [ .... ]
        type        (str) [DB .... EX]
        lat         (float64) [19.4 .... 35.4]
        lon         (float64) [-59.9 .... -59.5]
        vmax        (float64) [25.0 .... 50.0]
        mslp        (float64) [1014.0 .... 997.0]
        wmo_basin   (str) [north_atlantic .... north_atlantic]
    .
    More Information:
        id:              AL502021
        operational_id:  AL502021
        name:            Test
        source_info:     Custom User Data
        source:          custom
        ace:             3.8
        basin:           north_atlantic
        year:            2021
        season:          2021
        realtime:        False
        invest:          False
    """

    #Pop kwargs
    time_header = kwargs.pop('time_header',None)
    lat_header = kwargs.pop('lat_header',None)
    lon_header = kwargs.pop('lon_header',None)
    vmax_header = kwargs.pop('vmax_header',None)
    mslp_header = kwargs.pop('mslp_header',None)
    type_header = kwargs.pop('type_header',None)
    
    #Check for file extension
    netcdf = True if filepath[-3:] == '.nc' else False
    
    #Create empty dict
    data = {'id':storm_id,
            'operational_id':storm_id,
            'name':storm_name,
            'source_info':'Custom User Data',
            'source':'custom',
            'date':[],
            'extra_obs':[],
            'special':[],
            'type':[],
            'lat':[],
            'lon':[],
            'vmax':[],
            'mslp':[],
            'wmo_basin':[],
            'ace':0.0}

    #Parse text file
    if netcdf == False:
        
        #Store header data
        header = {}
        
        #Read file content
        f = open(filepath,"r")
        content = f.readlines()
        f.close()
        for line in content:
            if len(line) < 5: continue
            if line[0] in ['#','/']: continue
            line = line.split("\n")[0]
            line = line.split("\r")[0]
            
            #Split line
            if delimiter in ['',' ']: delimiter = None
            lineArray = line.split(delimiter)
            lineArray = [i.replace(" ","") for i in lineArray]
            
            #Determine header
            if len(header) == 0:
                for value in lineArray:
                    if value == time_header or value.lower() in ['time','date','valid_time','valid_date']:
                        header['date'] = [value,lineArray.index(value)]
                    elif value == lat_header or value.lower() in ['lat','latitude','lat_0']:
                        header['lat'] = [value,lineArray.index(value)]
                    elif value == lon_header or value.lower() in ['lon','longitude','lon_0']:
                        header['lon'] = [value,lineArray.index(value)]
                    elif value == vmax_header or value.lower() in ['vmax','wind','wspd','max_wind','wind_speed']:
                        header['vmax'] = [value,lineArray.index(value)]
                    elif value == mslp_header or value.lower() in ['mslp','slp','min_mslp','pressure','pres','minimum_mslp']:
                        header['mslp'] = [value,lineArray.index(value)]
                    elif value == type_header or value.lower() in ['type','storm_type']:
                        header['type'] = [value,lineArray.index(value)]
                found = [i in header.keys() for i in ['date','lat','lon','vmax','mslp']]
                if False in found: raise ValueError("Data must have columns for 'date', 'lat', 'lon', 'vmax' and 'mslp'.")
                continue
                
            #Enter standard data into dict
            enter_date = dt.strptime(lineArray[header.get('date')[1]],time_format)
            if enter_date in data['date']: raise ValueError("Error: Multiple entries detected for the same valid time.")
            data['date'].append(enter_date)
            data['lat'].append(float(lineArray[header.get('lat')[1]]))
            data['lon'].append(float(lineArray[header.get('lon')[1]]))
            data['vmax'].append(float(lineArray[header.get('vmax')[1]]))
            data['mslp'].append(float(lineArray[header.get('mslp')[1]]))
            
            #Derive storm type if needed
            if 'type' in header.keys():
                temp_type = lineArray[header.get('type')[1]]
                if temp_type in ['TY','ST']: temp_type = 'HU'
                data['type'].append(temp_type)
            else:
                data['type'].append(get_storm_type(data['vmax'][-1],False))
            
            #Derive ACE
            if data['date'][-1].strftime('%H%M') in constants.STANDARD_HOURS and data['type'][-1] in constants.NAMED_TROPICAL_STORM_TYPES:
                data['ace'] += accumulated_cyclone_energy(data['vmax'][-1])
            
            #Derive basin
            if len(data['wmo_basin']) == 0:
                data['wmo_basin'].append(get_basin(data['lat'][-1],data['lon'][-1],'north_atlantic'))
                data['basin'] = data['wmo_basin'][-1]
            else:
                data['wmo_basin'].append(get_basin(data['lat'][-1],data['lon'][-1],data['basin']))
            
            #Other entries
            extra_obs = 0 if data['date'][-1].strftime('%H%M') in constants.STANDARD_HOURS else 1
            data['extra_obs'].append(extra_obs)
            data['special'].append('')
        
        #Add other info
        data['year'] = data['date'][0].year
        data['season'] = data['date'][0].year
        
        #Return dict
        return data
    

#===========================================================================================================
# Private utilities
# These are primarily intended to be used internally. Do not add these to documentation.
#===========================================================================================================

def all_nan(arr):
    
    r"""
    Determine whether the entire array is filled with NaNs.
    
    Parameters
    ----------
    arr : list or numpy.ndarray
        List or array to be checked.
    
    Returns
    -------
    bool
        Returns whether the array is filled with all NaNs.
    """
    
    #Convert array to numpy array
    arr_copy = np.array(arr)
    
    #Check if there are non-NaN values in the array
    if len(arr_copy[~np.isnan(arr_copy)]) == 0:
        return True
    else:
        return False

def category_label_to_wind(category):
    
    r"""
    Convert Saffir-Simpson Hurricane Wind Scale category label to minimum threshold sustained wind speed in knots. Internal function.
    
    Parameters
    ----------
    category : int
        Saffir-Simpson Hurricane Wind Scale category. Use 0 for tropical storm, -1 for tropical depression.
    
    Returns
    -------
    int
        Sustained wind speed in knots corresponding to the minimum threshold of the requested category.
    """
    
    #Convert category to lowercase
    category_lowercase = category.lower()
    
    #Return thresholds based on category label
    if category_lowercase == 'td' or category_lowercase == 'sd':
        return category_to_wind(0) - 1
    elif category_lowercase == 'ts' or category_lowercase == 'ss':
        return category_to_wind(0)
    elif category_lowercase == 'c1':
        return category_to_wind(1)
    elif category_lowercase == 'c2':
        return category_to_wind(2)
    elif category_lowercase == 'c3':
        return category_to_wind(3)
    elif category_lowercase == 'c4':
        return category_to_wind(4)
    else:
        return category_to_wind(5)

def dynamic_map_extent(min_lon,max_lon,min_lat,max_lat,recon=False):

    r"""
    Sets up a dynamic map extent with an aspect ratio of 3:2 given latitude and longitude bounds.

    Parameters:
    -----------
    min_lon : float
        Minimum longitude bound.
    max_lon : float
        Maximum longitude bound.
    min_lat : float
        Minimum latitude bound.
    max_lat : float
        Maximum latitude bound.
    recon : bool
        Zoom in plots closer for recon plots.

    Returns:
    --------
    list
        List containing new west, east, north, south map bounds, respectively.
    """

    #Get lat/lon bounds
    bound_w = min_lon+0.0
    bound_e = max_lon+0.0
    bound_s = min_lat+0.0
    bound_n = max_lat+0.0

    #If only one coordinate point, artificially induce a spread
    if bound_w == bound_e:
        bound_w = bound_w - 0.6
        bound_e = bound_e + 0.6
    if bound_s == bound_n:
        bound_n = bound_n + 0.6
        bound_s = bound_s - 0.6

    #Function for fixing map ratio
    def fix_map_ratio(bound_w,bound_e,bound_n,bound_s,nthres=1.45):
        xrng = abs(bound_w-bound_e)
        yrng = abs(bound_n-bound_s)
        diff = float(xrng) / float(yrng)
        if diff < nthres: #plot too tall, need to make it wider
            goal_diff = nthres * (yrng)
            factor = abs(xrng - goal_diff) / 2.0
            bound_w = bound_w - factor
            bound_e = bound_e + factor
        elif diff > nthres: #plot too wide, need to make it taller
            goal_diff = xrng / nthres
            factor = abs(yrng - goal_diff) / 2.0
            bound_s = bound_s - factor
            bound_n = bound_n + factor
        return bound_w,bound_e,bound_n,bound_s

    #First round of fixing ratio
    bound_w,bound_e,bound_n,bound_s = fix_map_ratio(bound_w,bound_e,bound_n,bound_s,1.45)

    #Adjust map width depending on extent of storm
    xrng = abs(bound_e-bound_w)
    yrng = abs(bound_n-bound_s)
    factor = 0.1
    if min(xrng,yrng) < 15.0:
        factor = 0.2
    if min(xrng,yrng) < 12.0:
        factor = 0.4
    if min(xrng,yrng) < 10.0:
        factor = 0.6
    if min(xrng,yrng) < 8.0:
        factor = 0.75
    if min(xrng,yrng) < 6.0:
        factor = 0.9
    if recon: factor = factor * 0.3
    bound_w = bound_w-(xrng*factor)
    bound_e = bound_e+(xrng*factor)
    bound_s = bound_s-(yrng*factor)
    bound_n = bound_n+(yrng*factor)

    #Second round of fixing ratio
    bound_w,bound_e,bound_n,bound_s = fix_map_ratio(bound_w,bound_e,bound_n,bound_s,1.45)

    #Return map bounds
    return bound_w,bound_e,bound_s,bound_n

def read_url(url,split=True,subsplit=True):
    
    f = urllib.request.urlopen(url)
    content = f.read()
    content = content.decode("utf-8")
    if split: content = content.split("\n")
    if subsplit: content = [(i.replace(" ","")).split(",") for i in content]
    f.close()
    
    return content

class Distance:
    
    def __init__(self,dist,units='kilometers'):
        
        # Conversion fractions (numerator_denominator)
        mi_km = 0.621371
        nmi_km = 0.539957
        m_km = 1000.
        ft_km = 3280.84
        
        if units in ['kilometers','km']:
            self.kilometers = dist
        elif units in ['miles','mi']:
            self.kilometers = dist / mi_km
        elif units in ['nauticalmiles','nautical','nmi']:
            self.kilometers = dist / nmi_km
        elif units in ['feet','ft']:
            self.kilometers = dist / ft_km
        elif units in ['meters','m']:
            self.kilometers = dist / m_km
        self.miles = self.kilometers * mi_km
        self.nautical = self.kilometers * nmi_km
        self.meters = self.kilometers * m_km
        self.feet = self.kilometers * ft_km


class great_circle(Distance):

    def __init__(self, start_point, end_point, **kwargs):
        r"""
        
        Parameters
        ----------
        start_point : tuple or int
            Starting pair of coordinates, in order of (latitde, longitude)
        end_point : tuple or int
            Starting pair of coordinates, in order of (latitde, longitude)
        radius : float, optional
            Radius of Earth. Default is 6371.009 km.
        
        Returns
        -------
        great_circle
            Instance of a great_circle object. To retrieve the distance, add the requested unit at the end (e.g., "great_circle(start,end).kilometers").
        
        Notes
        -----
        Use spherical geometry to calculate the surface distance between two points. Uses the mean earth radius as defined by the International Union of Geodesy and Geophysics, approx 6371.009 km (for WGS-84), resulting in an error of up to about 0.5%. Otherwise set which radius of the earth to use by specifying a 'radius' keyword argument. It must be in kilometers.
        """
        
        #Set Earth's radius
        self.RADIUS = kwargs.pop('radius', 6371.009)
        
        #Compute 
        dist = self.measure(start_point,end_point)
        Distance.__init__(self,dist,units='kilometers')

    def measure(self, start_point, end_point):
        
        #Retrieve latitude and longitude coordinates from input pairs
        lat1, lon1 = math.radians(start_point[0]), math.radians(start_point[1]%360)
        lat2, lon2 = math.radians(end_point[0]), math.radians(end_point[1]%360)

        #Compute sin and cos of coordinates
        sin_lat1, cos_lat1 = math.sin(lat1), math.cos(lat1)
        sin_lat2, cos_lat2 = math.sin(lat2), math.cos(lat2)

        #Compute sin and cos of delta longitude
        delta_lon = lon2 - lon1
        cos_delta_lon, sin_delta_lon = math.cos(delta_lon), math.sin(delta_lon)

        #Compute great circle distance
        d = math.atan2(math.sqrt((cos_lat2 * sin_delta_lon) ** 2 +
                       (cos_lat1 * sin_lat2 -
                        sin_lat1 * cos_lat2 * cos_delta_lon) ** 2),
                sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_delta_lon)

        #Return great circle distance
        return self.RADIUS * d

r"""
This is a modified version of Cartopy's shapereader functionality, specified to directly read in an already-existing
Shapely object as opposed to expecting a local shapefile to be read in.
"""
import shapely.geometry as sgeom
import shapefile

class Record:
    """
    A single logical entry from a shapefile, combining the attributes with
    their associated geometry.

    """
    def __init__(self, shape, attributes, fields):
        self._shape = shape

        self._bounds = None
        # if the record defines a bbox, then use that for the shape's bounds,
        # rather than using the full geometry in the bounds property
        if hasattr(shape, 'bbox'):
            self._bounds = tuple(shape.bbox)

        self._geometry = None
        """The cached geometry instance for this Record."""

        self.attributes = attributes
        """A dictionary mapping attribute names to attribute values."""

        self._fields = fields

    def __repr__(self):
        return f'<Record: {self.geometry!r}, {self.attributes!r}, <fields>>'

    def __str__(self):
        return f'Record({self.geometry}, {self.attributes}, <fields>)'

    @property
    def bounds(self):
        """
        The bounds of this Record's :meth:`~Record.geometry`.

        """
        if self._bounds is None:
            self._bounds = self.geometry.bounds
        return self._bounds

    @property
    def geometry(self):
        """
        A shapely.geometry instance for this Record.

        The geometry may be ``None`` if a null shape is defined in the
        shapefile.

        """
        if not self._geometry and self._shape.shapeType != shapefile.NULL:
            self._geometry = sgeom.shape(self._shape)
        return self._geometry

class BasicReader:
    """
    Provide an interface for accessing the contents of a shapefile.

    The primary methods used on a Reader instance are
    :meth:`~Reader.records` and :meth:`~Reader.geometries`.

    """
    def __init__(self, reader):
        # Validate the filename/shapefile
        self._reader = reader
        if reader.shp is None or reader.shx is None or reader.dbf is None:
            raise ValueError("Incomplete shapefile definition "
                             "in '%s'." % filename)

        self._fields = self._reader.fields


    def close(self):
        return self._reader.close()

    def __len__(self):
        return len(self._reader)

    def geometries(self):
        """
        Return an iterator of shapely geometries from the shapefile.

        This interface is useful for accessing the geometries of the
        shapefile where knowledge of the associated metadata is not necessary.
        In the case where further metadata is needed use the
        :meth:`~Reader.records`
        interface instead, extracting the geometry from the record with the
        :meth:`~Record.geometry` method.

        """
        to_return = []
        for shape in self._reader.iterShapes():
            # Skip the shape that can not be represented as geometry.
            if shape.shapeType != shapefile.NULL:
                to_return.append(sgeom.shape(shape))
        return to_return

    def records(self):
        """
        Return an iterator of :class:`~Record` instances.

        """
        # Ignore the "DeletionFlag" field which always comes first
        to_return = []
        fields = self._reader.fields[1:]
        for shape_record in self._reader.iterShapeRecords():
            attributes = shape_record.record.as_dict()
            to_return.append(Record(shape_record.shape, attributes, fields))
        return to_return
