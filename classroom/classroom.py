import requests, pickle, os
from bs4 import BeautifulSoup


class bcolors:
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    SUCCESS = '\033[92m'
    INFO = '\033[94m'
    ENDC = '\033[0m'


show_msg = True  # False-ის შემთხვევაში არანაირი შეტყობინება არ დაიბეჭდება
show_logs = True  # False-ის შემთხვევაში არ დაიბეჭდება ლოგები


def log(value):
    if show_msg and show_logs:
        print("Log: ", value)


def success(value):
    if show_msg:
        print(bcolors.SUCCESS + str(value) + bcolors.ENDC)


def error(value):
    if show_msg:
        print(bcolors.ERROR + "Error: " + str(value) + bcolors.ENDC)


def warning(value):
    if show_msg:
        print(bcolors.WARNING + "Warning: " + str(value) + bcolors.ENDC)


class ClassroomParser():
    def __init__(self, session: requests.sessions.Session):
        self.__session = session
        self.__data = {}

    def getData(self):
        self.__parseCourses()
        self.parseMessages()
        return self.__data

    def __parseCourses(self):
        log("==== parsing courses ====")
        responce = self.__session.get("https://classroom.btu.edu.ge/ge/student/me/courses")
        soup = BeautifulSoup(responce.text, 'html.parser')
        td = soup.find('table')
        tr = td.find_all('tr')
        tr = tr[1:len(tr) - 1]

        data = []

        for item in tr:
            item = item.find_all('td')[2::]
            course = {}
            course_info = {}

            course_header = str(item[0]).replace('\t', '').split('\n')[1:3]
            course_info["course_index"] = int(course_header[0][9:len(course_header[0]) - 2].replace(
                'https://classroom.btu.edu.ge/ge/student/me/course/index/', ''))
            course_info["title"] = course_header[1][0:len(course_header[1]) - 4]

            course_info["score"] = '0'  # str(item[1])[4:len(item[1]) - 6].replace('\t', '').strip('\n')
            course_info["min_credit"] = str(item[2])[4:len(item[2]) - 6].replace('\t', '').strip('\n')
            course_info["credit"] = str(item[3])[4:len(item[3]) - 6].replace('\t', '').strip('\n')

            course['course_info'] = course_info
            course['course_scores'] = self.parseScores(course['course_info']['course_index'])

            scores_sum = .0
            for i in course['course_scores']:
                scores_sum += float(i['score'])
            course['course_info']['score'] = str(scores_sum)

            data.append(course)
        self.__data['courses'] = data
        log("==== courses parsed ====\n")

    def parseScores(self, course_index: int):
        log("Course_index( " + str(course_index) + " ) parsing scores ...")

        responce = self.__session.get(
            "https://classroom.btu.edu.ge/ge/student/me/course/scores/" + str(course_index))
        soup = BeautifulSoup(responce.text, 'html.parser')
        td = soup.find('table')
        tr = td.find_all('tr')
        tr = tr[1:len(tr) - 1]

        scores_table = []

        scores_sum = .0

        for item in tr:
            scores_item = {}

            item = str(item).replace('\t', '').split('\n')[2:6]
            del item[1:3]

            scores_item["title"] = item[0].replace('</td>', '')
            scores_item["score"] = item[1].replace('</div>', '')
            scores_sum += float(scores_item["score"])

            scores_table.append(scores_item)
        log("Course_index( " + str(course_index) + " ) scores parsed\n")
        return scores_table

    def parseMessages(self):
        log("==== parsing messages ====")
        responce = self.__session.get("https://classroom.btu.edu.ge/ge/messages/index/0/10000")
        soup = BeautifulSoup(responce.text, 'html.parser')
        td = soup.find('table')
        tr = td.find_all('tr')
        tr = tr[1::]

        messages = []

        for item in tr:
            message = {}

            item = str(item).replace('\t', '').split('\n')[:10]

            del item[1:5]
            del item[3]

            message["seen"] = False if item[0].replace('<tr class="', '').replace('">', '') == "info" else True
            message["id"] = \
                item[1].replace('<a href="https://classroom.btu.edu.ge/ge/messages/view/', '').replace('">', '').split(
                    '/')[0]
            message["author"] = item[2].replace('<strong>', '').replace('</strong>', '').replace('</a>', '')
            message["title"] = item[3].replace('<td>', '').replace('</td>', '')
            message["date"] = item[4].replace('<td>', '').replace('</td>', '')
            messages.append(message)
        self.__data['messages'] = messages
        log("==== messages parsed ====")

    def readMessage(self, id: int):
        log("parsing message content ====\n")
        responce = self.__session.get("https://classroom.btu.edu.ge/ge/messages/view/" + str(id))
        soup = BeautifulSoup(responce.text, 'html.parser')
        message = soup.find(id='message_body')
        message = str(message).replace('<div id="message_body">', '').replace('</div>', '')
        message = message.replace('&lt;', '<').replace('&gt;', '>')
        message = message.replace('<br/>', '')
        return message


class Classroom:
    def __init__(self):

        # ===== paths ==========
        self.__CookiePath = 'res/classroom.cookie'
        self.__ClassroomDataPath = './res/classroom.data'
        # ===== end of paths ===

        self.__session = requests.session()
        self.__data = {}

        self.__onStart()

    def logIn(self, email='', password='', remember=False):
        log("მომხმარებელი გადის ავტორიზაციას")
        if not self.checkIfLoggedIn():
            data = {
                'username': email,
                'password': password,
            }
            self.__session.post("https://classroom.btu.edu.ge/ge/login/trylogin", data=data)

            if self.checkIfLoggedIn():

                success("წარმატებით გაიარე ავტორიზაცია!")

                if remember:
                    self.__saveCookie()
                    log("ავტორიზაციის გავლის შემდეგ Cookie შეინახა")
                else:
                    log("ავტორიზაციის გავლის შემდეგ Cookie არ შეინახა")

                self.__onLogIn()
            else:
                error('მომხმარებელმა ვერ გაიარა ავტორიზაცია!')
        else:
            warning('მომხმარებელი უკვე ავტორიზებულია!')

    def logOut(self):
        if self.checkIfLoggedIn():
            self.__deleteCookie()
            self.__session.cookies = requests.session().cookies

            if not self.checkIfLoggedIn():
                log("მომხმარებელი გამოვიდა პროფილიდან")
        else:
            warning('მომხმარებელი არ არის ავტორიზებული!')

    def getAllData(self):
        log("მოაქვს ყველა მონაცემი")
        if self.checkIfLoggedIn():
            """
            ფუნქციის გამოძახეწბისას მონაცემები დაბრუნდება შემდეგი სახით:
                {
                    'courses':
                                [
                                    {
                                        'course_info':
                                                        {
                                                           'course_index': 'value',
                                                           'title': 'value,
                                                           'score': 'value',
                                                           'min_credit': 'value',
                                                           'credit': 'value'
                                                        }
                            
                                        'course_scores':
                                                        [
                                                            {
                                                                'title': 'value', 
                                                                'score': 'value'
                                                            },
                                                            {*****},
                                                            {*****},
                                                        ]
                                    },
                                    {*****},
                                    {*****},
                                ]
                            
                    'messages':
                                [
                                    {
                                        'seen': Boolean_value, 
                                        'id': 'value', 
                                        'author': 'value', 
                                        'title': 'value', 
                                        'date': 'value'
                                    },
                                    {*****},
                                    {*****},
                                ]
                }      
            """
            return self.__data
        else:
            error("ყველა მონაცემის წამოსაღებად საჭიროა ავტორიზაცია")

    def getCourses(self):
        log("მოაქვს კურსები")
        if self.checkIfLoggedIn():
            """
            ფუნქციის გამოძახეწბისას მონაცემები დაბრუნდება შემდეგი სახით:
                [
                    {
                        'course_info':
                                        {
                                           'course_index': 'value',
                                           'title': 'value,
                                           'score': 'value',
                                           'min_credit': 'value',
                                           'credit': 'value'
                                        }

                        'course_scores':
                                        [
                                            {
                                                'title': 'value', 
                                                'score': 'value'
                                            },
                                            {*****},
                                            {*****},
                                        ]
                    },
                    {*****},
                    {*****},
                ]

            """
            return self.__data['courses']
        else:
            error("კურსების წამოსაღებად საჭიროა ავტორიზაცია")

    def getMessages(self):
        log("მოაქვს შეტყობინებები")
        if self.checkIfLoggedIn():
            """
            ფუნქციის გამოძახეწბისას მონაცემები დაბრუნდება შემდეგი სახით:
                [
                    {
                        'seen': Boolean_value, 
                        'id': 'value', 
                        'author': 'value', 
                        'title': 'value', 
                        'date': 'value'
                    },
                    {*****},
                    {*****},
                ]

            """
            return self.__data['messages']
        else:
            error("შეტყობინებების წამოსაღებად საჭიროა ავტორიზაცია")

    def readMessage(self, id: int):

        # ფუნქციის  გამოძახების შემდეგ ბრუნდება შეტყობინების ტექსტი

        return ClassroomParser(self.__session).readMessage(id)

    def __onStart(self):
        self.__autoLognIn()

        if self.checkIfLoggedIn():
            self.__onLogIn()

    def __onLogIn(self):
        log("იტვირთება კლასრუმის საწყისი მონაცემები\n")
        self.__data = ClassroomParser(self.__session).getData()
        log("კლასრუმის საწყისი მონაცემები ჩაიტვირთა\n\n")

    def __autoLognIn(self):
        if self.__getCookie() != None:

            self.__session.cookies = self.__getCookie()

            if self.checkIfLoggedIn():

                success("ავტორიზაცია გაიარა Cookie-ს საშუალებით")
            else:

                error("Cookie არ არის ვალიდური, გაიარე ავტორიზაცია ხელახლა")
        else:

            log("ავტომატურად ვერ დაუკავშირდა")

    def checkIfLoggedIn(self):
        responce = self.__session.get("https://classroom.btu.edu.ge/ge/student/me/courses")
        soup = BeautifulSoup(responce.content, 'html.parser')
        if soup.find(id="balance_sum"):
            return True
        return False

    def __saveCookie(self):
        with open(self.__CookiePath, 'wb') as file:
            pickle.dump(self.__session.cookies, file)

    def __getCookie(self):
        try:
            with open(self.__CookiePath, 'rb') as file:
                return pickle.load(file)
        except:
            return None

    def __deleteCookie(self):
        try:
            if self.__getCookie():
                os.remove(self.__CookiePath)
                log("Cookie წაიშალა")
        except:
            pass

def is_btu_mail(mail : str):
    if "@btu.edu.ge" in mail:
        return True
    error("მითითებული მეილი არ არის BTU-ს მეილი")
    return False





if __name__ == "__main__":
    cl = Classroom()
    while not cl.checkIfLoggedIn():
        email = input('შეიყვანეთ მეილი \t:')
        if not is_btu_mail(email):
            continue
        password = input('შეიყვანეთ პაროლი \t:')
        cl.logIn(email, password, True)

    print(cl.getCourses())
    print(cl.getMessages())
    # print(cl.readMessage(ჩასვით შეტობინების ID აქ))
