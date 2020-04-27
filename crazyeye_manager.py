import sys,os




if __name__ == "__main__":
    #可以使用django的变量
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baoleiji.settings")
    import django
    django.setup()


    from  backend import main
    interactive_obj = main.ArgvHandler(sys.argv)
    interactive_obj.call()