#!/usr/bin/perl
use strict;
use warnings;
use 5.14.2;

use JSON;

my $conf = {
    todo_file_to_append_to => "$ENV{HOME}/documents/todo/aa_email_todo.txt",
    gmail_email_address    => 'your-email@gmail.com',
    gmail_password         => 'your-password', # and this is why the $confdir needs TIGHT permissions to restrict access, and also why you'd want a separate email account for this. If this is empty string or "ask" then the get_gmail_todo.py will prompt for the password.
    subject_prefix         => "TODOHOME",
    delete_messages        => "ask", # can only be either "ask", "yes" or "no" , as in what the script does with messages that get appended to the todo_file_to_append_to
};

my $json = JSON->new->allow_nonref;

my $confdir  = "$ENV{HOME}/.khaostodo/";

if ( ! -d $confdir ) {
    system("mkdir -p $confdir");
}

system ("chmod 700 $confdir") ; # just in case you forget to do this !

# the generated.gmail-todo.json will have to be :
#   cd $confdir
#   mv generated.gmail-todo.json gmail-todo.json
# and your going to need to make sure it has meaningful values.
burp ( "$confdir/generated.gmail-todo.json" , $json->encode( $conf ));

sub burp {
    my( $file_name ) = shift ;
    open( my $fh, ">$file_name" ) ||
        die "can't create $file_name $!" ;
    print $fh @_ ;
}

