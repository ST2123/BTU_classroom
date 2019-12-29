from classroom.classroom import Classroom , is_btu_mail ,error

cl = Classroom()

while not cl.checkIfLoggedIn():
    email = input('შეიყვანეთ მეილი \t:')
    if not is_btu_mail(email):
        continue
    password = input('შეიყვანეთ პაროლი \t:')
    cl.logIn(email, password, True)

courses = cl.getCourses()
messages = cl.getMessages()

for course in cl.getCourses():
    print()
    print(course['course_info'])

    for score in course['course_scores']:
        print("\t", score)

print()

for message in messages:
    print(message)

print()

while True:
    readmessage = False
    while True:
        answer = input("გინდა შეტყობინების წაკითხვა? (y/n): ")

        if answer == "n":
            readmessage = False
            break
        elif answer == "y":
            readmessage = True
            break
        else:
            error("შეიყვანე ან 'y' ან 'n'!")

    if readmessage:
        while True:
            try:
                message_id = int(input("შეიყვანე შეტყობინების id: "))
            except ValueError:
                error("შეიყვანე id")
            else:
                print(cl.readMessage(message_id))
                print()
                break
    else:
        break