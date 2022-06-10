#!/usr/bin/perl

        $| = 1;

        use JSON;
        use MIME::Lite;
        use Data::Dumper;
        use POSIX qw(strftime);

        my $timestamp = time();
        my %SMS = ();
        ${SMS}{'date'} = strftime "%Y%m%d%H%M%S", localtime( $timestamp );
        ${SMS}{'ip'} = ${ENV}{'REMOTE_ADDR'};
        my $inbound = 0;

        foreach my $name ( keys %ENV )
        {
                if( $name =~ /X_TELNYX_SIGNATURE/i )
                {
                        #
                        # found Telnyx header, flag it, parse the date/time from t=
                        #

                        $inbound = 1;

                        if( $ENV{$name} =~ /^t=(.*),h=.*$/ )
                        {
                                $timestamp = $1;
                                ${SMS}{'date'} = strftime "%Y%m%d%H%M%S", localtime( $timestamp );
                        }
                }
        }

        if( $ENV{REQUEST_METHOD} eq 'POST' )
        {
                my $query = undef;

                read( STDIN, $query, $ENV{CONTENT_LENGTH} );
                my $data = decode_json( $query );

        if( $inbound == 0 )
        {
                        #
                        # outbound confirmation
                        #
                        my $logdata = sprintf( "%s:%s:%s", ${SMS}{'ip'}, ${data}->{data}->{payload}->{to}[0]->{phone_number}, ${data}->{data}->{payload}->{to}[0]->{status} );
                        &logit( $logdata );
                }
                else
                {
                        #
                        # inbound
                        #
                        ${SMS}{'id'} = $data->{'sms_id'};
                        ${SMS}{'from'} = $data->{'from'};
                        ${SMS}{'to'} = $data->{'to'};
                        ${SMS}{'body'} = $data->{'body'};

                        #
                        # send the SMS as an email
                        #
                        &sendmail( %SMS );
                }
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
                my %email = ();
                ${email}{'from'} = 'sms@brampton.net';
                ${email}{'to'} = "jp" . ${sms}{'to'} . '@brampton.net';
                ${email}{'subject'} = 'SMS Message Received from ' . ${sms}{'from'};

                my $data = sprintf( "From: %s\nTo: %s\nCreated: %s\n\n%s", ${sms}{'from'}, ${sms}{'to'}, ${sms}{'date'}, ${sms}{'body'} );
                my $logdata = sprintf( "%s:%s:%s:%s:%s", ${sms}{'ip'}, ${sms}{'id'}, ${sms}{'from'}, ${sms}{'to'}, ${sms}{'date'} );

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

