from hieronymus import _progs


def main(args=None):
    prog = _progs.Prog(args=args)
    prog.run()

if __name__ == '__main__':
    main()