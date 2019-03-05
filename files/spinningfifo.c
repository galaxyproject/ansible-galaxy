#include <uwsgi.h>

static int spinningfifo_hook(char *arg) {
        int fd;
        char *space = strchr(arg, ' ');
        if (!space) {
                uwsgi_log("invalid hook spinningfifo syntax, must be: <file> <string>\n");
                return -1;
        }
        *space = 0;
retry:
        uwsgi_log("waiting for %s ...\n", arg);
        fd = open(arg, O_WRONLY|O_NONBLOCK);
        if (fd < 0) {
                if (errno == ENODEV || errno == ENOENT) {
                        sleep(1);
                        goto retry;
                }
#ifdef ENXIO
                if (errno == ENXIO) {
                        sleep(1);
                        goto retry;
                }
#endif
                uwsgi_error_open(arg);
                *space = ' ';
                return -1;
        }
        *space = ' ';
        size_t l = strlen(space+1);
        if (write(fd, space+1, l) != (ssize_t) l) {
                uwsgi_error("spinningfifo_hook()/write()");
                close(fd);
                return -1;
        }
        close(fd);
        return 0;
}


static void register_hooks() {
        uwsgi_register_hook("spinningfifo", spinningfifo_hook);
}

struct uwsgi_plugin spinningfifo_plugin = {
        .name = "spinningfifo",
        .on_load = register_hooks,
};