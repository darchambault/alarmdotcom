[Alarm.com Custom Component](https://github.com/darchambault/alarmdotcomredux) for Home Assistant

# What This Is:

This is a custom component to allow Home Assistant to interface with the [Alarm.com](https://www.alarm.com/) site by scraping the Alarm.com web portal. This component is designed to integrate the Alarm.com security system functionality only - it requires an Alarm.com package which includes security system support, and it supports only partial Alarm.com home automation functionality. Please note that Alarm.com may remove access at any time.

- Note that some providers are now requiring 2FA. If you have problem signing in and your web portal keeps nagging you to setup 2FA, please follow the instructions in the Two Factor Authentication section below.

## Installation / Usage with Home Assistant

1. Download this project as a zip file using GitHub's Clone or Download button at the top-right corner of the main project page.
2. Extract the contents locally.
3. Copy the directory alarmdotcomredux to config/custom_components/alarmdotcomredux on your HA installation.
4. Configure through the Integrations page

## Configuration

## Two Factor Authentication

Some providers (ADT and Protection1) are starting to require 2FA for logins. This can be worked around by getting the `twoFactorAuthenticationId` cookie from an already authenticated browser and entering it as a configuration parameter.

Simple steps to get the cookie:

    1) Log in to your account on the Alarm.com website: https://www.alarm.com/login.aspx
    2) Enable Two Factor Authentication
    3) Once you are fully logged in to the alarm.com portal without any more 2FA nag screens, go into the developer tools in your browser and locate the `twoFactorAuthenticationId` cookie. Instructions for locating the cookie in Chrome can be found here: https://developers.google.com/web/tools/chrome-devtools/storage/cookies
    4) Copy the cookie string into the "2FA Cookie" field of your integration's configuration.

## Multiple Alarm.com Installations

Multiple Alarm.com installations are supported by adding the integration as many times as needed through the Integrations page.
