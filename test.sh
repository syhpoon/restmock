#!/bin/bash
#
# Basic actions tests
#

set -e

ok='\e[0;32m'
err='\e[0;31m'
n='\e[0m'

echo -n "* BODY match test.."
[[ "$(curl -X POST -d '<tag>INSIDE BODY</tag>' http://localhost:8000/ 2> /dev/null)" == 'BODY match test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* BODY eq test.."
[[ "$(curl -v -X POST -d 'THE WHOLE BODY' http://localhost:8000/ 2> /dev/null)" == 'BODY eq test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* URL match test.."
[[ "$(curl -X GET http://localhost:8000/a/b/c/d 2> /dev/null)" == 'URL match test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* URL eq test.."
[[ "$(curl -X GET http://localhost:8000/a/b/c 2> /dev/null)" == 'URL eq test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* PARAM match test.."
[[ "$(curl -X GET http://localhost:8000/?x=aawtfbb 2> /dev/null)" == 'PARAM match test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* PARAM eq test.."
[[ "$(curl -X GET 'http://localhost:8000/?x=abc&y=yval' 2> /dev/null)" == 'PARAM eq test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* Complex test.."
[[ "$(curl -X PUT -d 'BODY' 'http://localhost:8000/complex/test/1?param1=a&param2=b' 2> /dev/null)" == 'Complex test result' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* Substitute test.."
[[ "$(curl -X GET 'http://localhost:8000/substitute?a=111' 2> /dev/null)" == 'Here goes query param a: 111' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"

echo -n "* No match.."
[[ "$(curl -v -X GET http://localhost:8000 2> /dev/null)" == '' ]] && echo -e "${ok}OK${n}" || echo -e "${err}NOK${n}"
