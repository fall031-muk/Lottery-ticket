import random
import requests

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView



class GetLottoNumber(APIView):

    def get(self, request):
        lotto_round = request.GET.get('lotto_round')
        lotto_url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo=" + str(lotto_round)
        lotto_response = requests.get(lotto_url)
        print(lotto_response)
        # {"totSellamnt": 88625160000, "returnValue": "success", "drwNoDate": "2020-03-21", "firstWinamnt": 1684582212,
        #  "drwtNo6": 28, "drwtNo4": 21, "firstPrzwnerCo": 13, "drwtNo5": 22, "bnusNo": 45, "firstAccumamnt": 21899568756,
        #  "drwNo": 903, "drwtNo2": 15, "drwtNo3": 16, "drwtNo1": 2}
        lotto_number = random.sample(range(1, 46), 6)
        lotto_number.sort()
        return Response(lotto_number, status=status.HTTP_200_OK)
