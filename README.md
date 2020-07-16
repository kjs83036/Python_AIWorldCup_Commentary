# Python_AIWorldCup_Commentary
KAIST 주최 AI 월드컵 해설 부문

**/코드/commentator_skeleton.py 파일을 test_world-develop/examples에 넣고 테스트 환경을 실행하여 재현 가능(ppt)참고

![image](https://user-images.githubusercontent.com/26050767/87285043-01f39a00-c532-11ea-8e24-2868096f7ccb.png)
![image](https://user-images.githubusercontent.com/26050767/87285058-0750e480-c532-11ea-959c-89c7eb747646.png)
![image](https://user-images.githubusercontent.com/26050767/87285089-1041b600-c532-11ea-9196-00ffed634d56.png)
![image](https://user-images.githubusercontent.com/26050767/87285105-146dd380-c532-11ea-8a80-1d252cb90aa9.png)

2. 환경 세팅 및 해설 실행
	1. 리눅스 설치
		a. usb 세팅 및 설치
			i. rufusUSB를 통해 부팅 USB생성
			ii. boot영역, swap 영역 세팅
	2. 실행환경 설치
		a. webot R2019b설치
	3. 그래픽드라이버 설치
	4. anaconda 설치
		a. anaconda python을 기본 python으로(재부팅)
		b. pip install autobahn==19.8.1 설치
		c. pip install msgpack-python==0.5.6 설치
		d. pip install twisted==19.7.0 설치
	5. testworld git clone
		a. git clone https://github.com/aiwc/test_world.git --recurse-submodules
	6. commentator_skeleton.py 교체
		a. https://github.com/kjs83036/Python_AIWorldCup_Commentary/tree/master/코드에서 commentator_skeleton.py 다운로드
		b. test_world/examples/commentator_skeleton_py/commentator_skeleton.py 파일에 덮어 쓰기
		c. 외부 파일 실행 가능 권한 부여
	7. 4개 파일 연결 파이썬 아나콘다로 교체
		a. commentator_skeleton.py의 헤더의 #!/home/sktlrkan/anaconda3/bin/python 경로 중 sktlrkan를 해당 ubuntu user의 이름으로 변경
		b. ex) #!/home/이름/anaconda3/bin/python
		c. test_world/examples/player_rulebased-A_py/player_rulebased-A.py
		d. test_world/examples/player_rulebased-B_py/player_rulebased-B.py
		e. test_world/examples/reporter_skeleton_py/reporter_skeleton.py
		f. 위 3파일의 헤더 또한 #!/home/이름/anaconda3/bin/python으로 변경
	8. webot설정
		a. webot실행 후 Ctrl + 2를 눌러 오른쪽에 text editor를 띄움
		b. text editor의 불러오기 기능활용하여controllers/soccer_robot/soccer_robot.cpp를 로드
		c. f7을 눌러 빌드
		d. controllers/soccer_robot/soccer_robot.cpp와plugins/physics/collision_detector/collision_detector.cpp파일 또한 같은 방식으로 빌드
		e. 총 3개의 파일을 빌드
	9. 재생버튼으로 경기 시작

