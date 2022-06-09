#!/usr/bin/perl

        #
        # my suggestion is to create a directory using your Telnyx profile id
        # to obfuscate the URL, for example
        #
        # https://somedomain.com/4041808a-8911-4a9e-9b5e-70ed906567de/sms.cgi
        #
        # It is highly unlikely anyone is going to know the path to sms.cgi
        #

        $| = 1;

        use JSON;
        use MIME::Lite;
        use POSIX qw(strftime);

        my $timestamp = time();
        my %SMS = ();
        ${SMS}{'date'} = strftime "%Y%m%d%H%M%S", localtime( $timestamp );
        my $telnyx = 0;

        foreach my $name ( keys %ENV )
        {
                if( $name =~ /X_TELNYX_SIGNATURE/i )
                {
                        #
                        # found Telnyx header, flag it, parse the date/time from t=
                        #

                        $telnyx = 1;

                        if( $ENV{$name} =~ /^t=(.*),h=.*$/ )
                        {
                                $timestamp = $1;
                                ${SMS}{'date'} = strftime "%Y%m%d%H%M%S", localtime( $timestamp );
                                ${SMS}{'ip'} = ${ENV}{'REMOTE_ADDR'};
                        }
                }
        }

        #if( $telnyx == 0 )
        #{
                #
                # no Telnyx header, redirect them, this is not a valid connection
                # it is unlikely we'll ever see this if you use profile id
                #

         #      &logit( "connection:" . ${ENV}{'REMOTE_ADDR'} . ":invalid:redirected" );
         #      print "Location: https://google.com\n\n";
         #      exit;
        #}

        if( $ENV{REQUEST_METHOD} eq 'POST' )
        {
                my $query = undef;

                read( STDIN, $query, $ENV{CONTENT_LENGTH} );
                my $data = decode_json( $query );

                ${SMS}{'id'} = $data->{'sms_id'};
                ${SMS}{'from'} = $data->{'from'};
                ${SMS}{'to'} = $data->{'to'};
                ${SMS}{'body'} = $data->{'body'};

                #
                # send the SMS as an email
                #

                &sendmail( %SMS );
        }

        #
        # send back a 200 response with OK
        #

        print "Content-Type: text/html\n\nOK\n";
        exit;

        #
        # end of script
        #

        sub sendmail( $ )
        {
                my ( %sms ) = @_;
                my $data = sprintf( "From: %s\nTo: %s\nCreated: %s\n\n%s", ${sms}{'from'}, ${sms}{'to'}, ${sms}{'date'}, ${sms}{'body'} );
                my $logdata = sprintf( "%s:%s:%s:%s:%s", ${sms}{'ip'}, ${sms}{'id'}, ${sms}{'from'}, ${sms}{'to'}, ${sms}{'date'} );

                my %email = ();
                ${email}{'from'} = 'sms@yourdomain.com';
                ${email}{'to'} = 'someuser@yourdomain.com';
                ${email}{'subject'} = 'SMS Message Received from ' . ${sms}{'from'};

                $msg = MIME::Lite->new(
                                                                From     => ${email}{'from'},
                                                                To       => ${email}{'to'},
                                                                Subject  => ${email}{'subject'},
                                                                Data     => $data
                                                        );

                #
                # send the message
                #

                $msg->send;

                #
                # log email success/failure
                #

                &logit( sprintf( "%s:%s", $logdata, $msg->last_send_successful ? "smtpOK" : "smtpNOTOK"  ));
        }

        sub logit( $ )
        {
                my ( $txt ) = @_;
                my $DATE = `date +"%Y%m%d%H%M%S"`;
                chomp( $DATE );
                open( LOG, ">>/tmp/sms.log" );
                print LOG ${DATE} . ":" . $txt . "\n";
                close( LOG );
        }

