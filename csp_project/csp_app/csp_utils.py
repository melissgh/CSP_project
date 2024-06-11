from datetime import datetime, timedelta
from collections import defaultdict
from .models import TimetableSlot

# Données initiales
MODULES = [
    'Securite_lecture', 'Securite_td', 'Methodes_formelles_lecture', 'Methodes_formelles_td',
    'Analyse_numerique_lecture', 'Analyse_numerique_td', 'Entrepreneuriat_lecture',
    'Recherche_operationnelle_lecture', 'Recherche_operationnelle_td',
    'Distributed_architecture_lecture', 'Distributed_architecture_td',
    'Reseaux_lecture', 'Reseaux_td', 'Reseaux_tp', 'AI_lecture', 'AI_td', 'AI_tp'
]

TEACHERS = {
    'Mme. Zaidi': ['Reseaux_tp'],
    'Dr. Issadi': ['Recherche_operationnelle_lecture', 'Recherche_operationnelle_td'],
    'Dr. Zedek': ['Methodes_formelles_lecture', 'Methodes_formelles_td'],
    'Mr. Sahli': ['Reseaux_td'],
    'Mme. Hamma': ['AI_tp'],
    'Dr. Djenadi': ['Distributed_architecture_lecture', 'Distributed_architecture_td'],
    'Dr. Lekehali': ['AI_lecture', 'AI_td'],
    'Dr. Alkama': ['Analyse_numerique_lecture', 'Analyse_numerique_td'],
    'Dr. Kaci': ['Entrepreneuriat_lecture'],
    'M. Abbas && Mme. Ladlani': ['AI_tp'],
    'Mme. Djenane': ['Securite_td'],
    'Dr. Zenadji': ['Reseaux_lecture', 'Reseaux_td'],
    'Mme. Khelouf': ['Securite_td'],
    'Mme. Kassa': ['Securite_td'],
    'Dr. Saba': ['Analyse_numerique_td'],
    'Dr. Djebari': ['Securite_lecture'],
    'M. Bechar': ['AI_tp']
}

GROUPS = [f'Group{num}' for num in range(1, 7)]
TD_ROOMS = [f"TD{room}" for room in range(1, 26)]
TP_ROOMS = [f"TP{room}" for room in range(1, 12)]
LECTURE_ROOMS = [f"Amphi{room}" for room in range(7, 8)]
CLASSROOMS = TD_ROOMS + TP_ROOMS + LECTURE_ROOMS
DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']

# Fonction pour générer les créneaux horaires
def generate_time_slots():
    start_time = datetime.strptime("08:30", "%H:%M").time()
    slots = []
    for i in range(5):  # 5 sessions par jour
        end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=90)).time()
        slots.append((start_time.strftime("%H:%M"), f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"))
        start_time = (datetime.combine(datetime.today(), end_time) + timedelta(minutes=10)).time()
    return slots

# Fonction pour générer l'emploi du temps
def generate_timetable():
    slots = []
    lecture_modules = [module for module in MODULES if '_lecture' in module]
    other_modules = [module for module in MODULES if '_lecture' not in module]

    # Suivi des sessions assignées à chaque groupe et enseignant
    sessions_assigned_per_group = {group: [] for group in GROUPS}
    sessions_assigned_per_teacher = {teacher: [] for teacher in TEACHERS.keys()}
    lectures_per_day_per_group = {group: {day: 0 for day in DAYS} for group in GROUPS}
    lectures_per_day_per_teacher = {teacher: {day: 0 for day in DAYS} for teacher in TEACHERS.keys()}
    days_worked_per_teacher = {teacher: set() for teacher in TEACHERS.keys()}

    # Suivi de l'utilisation des salles de classe
    classroom_usage = {day: {slot: [] for slot in TIME_SLOTS} for day in DAYS}

    # Fonction pour vérifier les contraintes des créneaux consécutifs
    def check_consecutive_slots(entity_sessions, day, slot_index):
        return (
            len(entity_sessions) >= 2 and
            (day, slot_index - 1) in entity_sessions and
            (day, slot_index - 2) in entity_sessions
        )

    # Fonction pour vérifier si l'enseignant peut travailler un jour supplémentaire
    def can_teacher_work_additional_day(teacher, day):
        return len(days_worked_per_teacher[teacher]) < 2 or day in days_worked_per_teacher[teacher]

    # Assignation des sessions
    for day in DAYS:
        for slot_index, slot in enumerate(TIME_SLOTS):
            if day == 'Tuesday' and slot_index >= 3:
                break  # Arrêter après la troisième session le mardi

            # Assignation des lectures
            if lecture_modules:
                module = lecture_modules.pop(0)
                teacher = next((t for t, modules in TEACHERS.items() if module in modules), None)
                if teacher:
                    for classroom in LECTURE_ROOMS:
                        if classroom not in classroom_usage[day][slot] and can_teacher_work_additional_day(teacher, day):
                            if all(lectures_per_day_per_group[group][day] < 2 for group in GROUPS) and \
                                    lectures_per_day_per_teacher[teacher][day] < 2:
                                slots.append(TimetableSlot.objects.create(
                                    day=day,
                                    start_time=slot,
                                    module_name=module,
                                    teacher_name=teacher,
                                    group_name="; ".join(GROUPS),  # Tous les groupes
                                    classroom_name=classroom
                                ))
                                for group in GROUPS:
                                    sessions_assigned_per_group[group].append((day, slot_index))
                                    lectures_per_day_per_group[group][day] += 1
                                sessions_assigned_per_teacher[teacher].append((day, slot_index))
                                lectures_per_day_per_teacher[teacher][day] += 1
                                days_worked_per_teacher[teacher].add(day)
                                classroom_usage[day][slot].append(classroom)
                                break

            # Assignation des sessions TD et TP
            for module in other_modules:
                if module.endswith('_td') or module.endswith('_tp'):
                    teacher = next((t for t, modules in TEACHERS.items() if module in modules), None)
                    if teacher:
                        for classroom in (TD_ROOMS if module.endswith('_td') else TP_ROOMS):
                            if classroom not in classroom_usage[day][slot] and can_teacher_work_additional_day(teacher, day):
                                for group in GROUPS:
                                    # Vérifier si le groupe a déjà une session à ce moment-là
                                    if not any(s[0] == day and s[1] == slot_index for s in sessions_assigned_per_group[group]):
                                        # Vérifier si l'enseignant a déjà une session à ce moment-là
                                        if not any(s[0] == day and s[1] == slot_index for s in sessions_assigned_per_teacher[teacher]):
                                            slots.append(TimetableSlot.objects.create(
                                                day=day,
                                                start_time=slot,
                                                module_name=module,
                                                teacher_name=teacher,
                                                group_name=group,
                                                classroom_name=classroom
                                            ))
                                            sessions_assigned_per_group[group].append((day, slot_index))
                                            sessions_assigned_per_teacher[teacher].append((day, slot_index))
                                            days_worked_per_teacher[teacher].add(day)
                                            classroom_usage[day][slot].append(classroom)
                                            break

            # Vérification des créneaux consécutifs
            for teacher, sessions in sessions_assigned_per_teacher.items():
                if check_consecutive_slots(sessions, day, slot_index):
                    # Supprimer la dernière session assignée
                    last_session = sessions[-1]
                    slots = [s for s in slots if not (s.day == last_session[0] and s.start_time == TIME_SLOTS[last_session[1]])]
                    for group in GROUPS:
                        if (last_session[0], last_session[1]) in sessions_assigned_per_group[group]:
                            sessions_assigned_per_group[group].remove((last_session[0], last_session[1]))
                    sessions_assigned_per_teacher[teacher].remove((last_session[0], last_session[1]))
                    days_worked_per_teacher[teacher].discard(last_session[0])

            for group, sessions in sessions_assigned_per_group.items():
                if check_consecutive_slots(sessions, day, slot_index):
                    # Supprimer la dernière session assignée
                    last_session = sessions[-1]
                    slots = [s for s in slots if not (s.day == last_session[0] and s.start_time == TIME_SLOTS[last_session[1]])]
                    sessions_assigned_per_group[group].remove((last_session[0], last_session[1]))
                    for teacher in TEACHERS.keys():
                        if (last_session[0], last_session[1]) in sessions_assigned_per_teacher[teacher]:
                            sessions_assigned_per_teacher[teacher].remove((last_session[0], last_session[1]))
                            days_worked_per_teacher[teacher].discard(last_session[0])

    return slots

# Générer les créneaux horaires
TIME_SLOTS = [slot[0] for slot in generate_time_slots()]

# Générer l'emploi du temps
generate_timetable()



# from datetime import datetime, timedelta
# from .models import TimetableSlot

# MODULES = [
#     'Securite_lecture', 'Securite_td', 'Methodes_formelles_lecture', 'Methodes_formelles_td',
#     'Analyse_numerique_lecture', 'Analyse_numerique_td', 'Entrepreneuriat_lecture',
#     'Recherche_operationnelle_lecture', 'Recherche_operationnelle_td',
#     'Distributed_architecture_lecture', 'Distributed_architecture_td',
#     'Reseaux_lecture', 'Reseaux_td', 'Reseaux_tp', 'AI_lecture', 'AI_td', 'AI_tp'
# ]

# TEACHERS = {
#     'Mme. Zaidi': ['Reseaux_tp'],
#     'Dr. Issadi': ['Recherche_operationnelle_lecture', 'Recherche_operationnelle_td'],
#     'Dr. Zedek': ['Methodes_formelles_lecture', 'Methodes_formelles_td'],
#     'Mr. Sahli': ['Reseaux_td'],
#     'Mme. Hamma': ['AI_tp'],
#     'Dr. Djenadi': ['Distributed_architecture_lecture', 'Distributed_architecture_td'],
#     'Dr. Lekehali': ['AI_lecture', 'AI_td'],
#     'Dr. Alkama': ['Analyse_numerique_lecture', 'Analyse_numerique_td'],
#     'Dr. Kaci': ['Entrepreneuriat_lecture'],
#     'M. Abbas && Mme. Ladlani': ['AI_tp'],
#     'Mme. Djenane': ['Securite_td'],
#     'Dr. Zenadji': ['Reseaux_lecture', 'Reseaux_td'],
#     'Mme. Khelouf': ['Securite_td'],
#     'Mme. Kassa': ['Securite_td'],
#     'Dr. Saba': ['Analyse_numerique_td'],
#     'Dr. Djebari': ['Securite_lecture'],
#     'M. Bechar': ['AI_tp']
# }

# GROUPS = [f'Group{num}' for num in range(1, 7)]
# TD_ROOMS = [f"TD{room}" for room in range(1, 26)]
# TP_ROOMS = [f"TP{room}" for room in range(1, 12)]
# LECTURE_ROOMS = [f"Amphi{room}" for room in range(7, 8)]
# CLASSROOMS = TD_ROOMS + TP_ROOMS + LECTURE_ROOMS
# DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']

# def generate_time_slots():
#     start_time = datetime.strptime("08:30", "%H:%M").time()
#     slots = []
#     for i in range(5):  # 5 sessions per day
#         end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=90)).time()
#         slots.append((start_time.strftime("%H:%M"), f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"))
#         start_time = (datetime.combine(datetime.today(), end_time) + timedelta(minutes=10)).time()
#     return slots

# def generate_timetable():
#     slots = []
#     lecture_modules = [module for module in MODULES if '_lecture' in module]
#     other_modules = [module for module in MODULES if '_lecture' not in module]

#     # Track the sessions assigned to each group and teacher
#     sessions_assigned_per_group = {group: [] for group in GROUPS}
#     sessions_assigned_per_teacher = {teacher: [] for teacher in TEACHERS.keys()}
#     lectures_per_day_per_group = {group: {day: 0 for day in DAYS} for group in GROUPS}
#     lectures_per_day_per_teacher = {teacher: {day: 0 for day in DAYS} for teacher in TEACHERS.keys()}

#     # Track classroom usage
#     classroom_usage = {day: {slot: [] for slot in TIME_SLOTS} for day in DAYS}

#     # Assign lectures and other sessions
#     for day in DAYS:
#         for slot_index, slot in enumerate(TIME_SLOTS):
#             if day == 'Tuesday' and slot_index >= 3:
#                 break  # Stop generating slots after the third session on Tuesday

#             # Assign lectures
#             if lecture_modules:
#                 module = lecture_modules.pop(0)
#                 teacher = None
#                 for t, modules in TEACHERS.items():
#                     if module in modules:
#                         teacher = t
#                         break
#                 if teacher:
#                     for classroom in LECTURE_ROOMS:
#                         if classroom not in classroom_usage[day][slot]:
#                             if not any(s[0] == day and s[1] == slot_index for s in sessions_assigned_per_teacher[teacher]) and \
#                                     all(lectures_per_day_per_group[group][day] < 2 for group in GROUPS) and \
#                                     lectures_per_day_per_teacher[teacher][day] < 2:
#                                 slots.append(TimetableSlot.objects.create(
#                                     day=day,
#                                     start_time=slot,
#                                     module_name=module,
#                                     teacher_name=teacher,
#                                     group_name="; ".join(GROUPS),  # All groups
#                                     classroom_name=classroom
#                                 ))
#                                 for group in GROUPS:
#                                     sessions_assigned_per_group[group].append((day, slot_index))
#                                     lectures_per_day_per_group[group][day] += 1
#                                 sessions_assigned_per_teacher[teacher].append((day, slot_index))
#                                 lectures_per_day_per_teacher[teacher][day] += 1
#                                 classroom_usage[day][slot].append(classroom)
#                                 break

#             # Assign TD and TP sessions
#             for module in other_modules:
#                 if module.endswith('_td') or module.endswith('_tp'):
#                     teacher = None
#                     for t, modules in TEACHERS.items():
#                         if module in modules:
#                             teacher = t
#                             break
#                     if teacher:
#                         for classroom in (TD_ROOMS if module.endswith('_td') else TP_ROOMS):
#                             if classroom not in classroom_usage[day][slot]:
#                                 for group in GROUPS:
#                                     # Check if the group already has a session at this time and day
#                                     if not any(s[0] == day and s[1] == slot_index for s in sessions_assigned_per_group[group]):
#                                         # Check if the teacher already has a session at this time and day
#                                         if not any(s[0] == day and s[1] == slot_index for s in sessions_assigned_per_teacher[teacher]):
#                                             slots.append(TimetableSlot.objects.create(
#                                                 day=day,
#                                                 start_time=slot,
#                                                 module_name=module,
#                                                 teacher_name=teacher,
#                                                 group_name=group,
#                                                 classroom_name=classroom
#                                             ))
#                                             sessions_assigned_per_group[group].append((day, slot_index))
#                                             sessions_assigned_per_teacher[teacher].append((day, slot_index))
#                                             classroom_usage[day][slot].append(classroom)
#                                             break

#             # Check if a teacher or group has more than three consecutive sessions
#             if slot_index >= 2:
#                 for teacher, sessions in sessions_assigned_per_teacher.items():
#                     if len(sessions) >= 3 and all((day, i) in sessions for i in range(slot_index - 2, slot_index + 1)):
#                         # Remove the last session from the assigned sessions
#                         last_session = sessions[-1]
#                         slots = [s for s in slots if not (s.day == last_session[0] and s.start_time == TIME_SLOTS[last_session[1]])]
#                         for group in GROUPS:
#                             if (last_session[0], last_session[1]) in sessions_assigned_per_group[group]:
#                                 sessions_assigned_per_group[group].remove((last_session[0], last_session[1]))
#                         sessions_assigned_per_teacher[teacher].remove((last_session[0], last_session[1]))

#                 for group, sessions in sessions_assigned_per_group.items():
#                     if len(sessions) >= 3 and all((day, i) in sessions for i in range(slot_index - 2, slot_index + 1)):
#                         # Remove the last session from the assigned sessions
#                         last_session = sessions[-1]
#                         slots = [s for s in slots if not (s.day == last_session[0] and s.start_time == TIME_SLOTS[last_session[1]])]
#                         sessions_assigned_per_group[group].remove((last_session[0], last_session[1]))
#                         for teacher in TEACHERS.keys():
#                             if (last_session[0], last_session[1]) in sessions_assigned_per_teacher[teacher]:
#                                 sessions_assigned_per_teacher[teacher].remove((last_session[0], last_session[1]))

#     return slots

# TIME_SLOTS = [slot[0] for slot in generate_time_slots()]

# generate_timetable()
